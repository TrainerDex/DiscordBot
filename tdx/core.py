import datetime
import humanize
import logging
import os
import requests
from typing import Union

import discord
from redbot.core import checks, commands, Config
from redbot.core.bot import Red

import trainerdex
from tdx.converters import DateConverter, TeamConverter

log = logging.getLogger("red.tdx.core")
POGOOCR_TOKEN_PATH = os.path.join(os.path.dirname(__file__), 'data/key.json')


class TrainerDexCore(commands.Cog):
    """TrainerDex Core Functionality"""
    
    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config = Config.get_conf(self, identifier=8124637339)  # TrainerDex on a T9 keyboard
        self.client = None
        
        assert os.path.isfile(POGOOCR_TOKEN_PATH)  # Looks for a Google Cloud Token
        
        self.global_defaults = {
            'embed_footer': 'Provided with ❤️ by TrainerDex',
            'notice': None,
        }
        self.guild_defaults = {
            'emoji_success': "✅",
            'emoji_failure': "❌",
            'emoji_warning': "⚠️",
            'emoji_notice': "⚠️",
            'emoji_loading': "<a:loading:471298325904359434>",
            'assign_roles_on_join': True,
            'set_nickname_on_join': True,
            'set_nickname_on_update': True,
        }
        
        self.config.register_global(**self.global_defaults)
        self.config.register_guild(**self.guild_defaults)
    
    async def initialize(self) -> None:
        await self._create_client()
    
    async def _create_client(self) -> None:
        """Create TrainerDex API Client"""
        token = await self._get_token()
        self.client = trainerdex.Client(token=token, identifier='ts_social_discord')
    
    async def _get_token(self) -> str:
        """Get TrainerDex token"""
        api_tokens = await self.bot.get_shared_api_tokens("trainerdex")
        token = api_tokens.get("token", "")
        if not token:
            log.warning("No valid token found")
        return token
    
    async def get_trainer(self, value: Union[discord.Member, discord.User, str, int] = None) -> Trainer:
        if isinstance(value, str):
            return self.client.get_trainer_from_username(value)
        elif isinstance(value, (discord.Member, discord.User)):
            try:
                return self.client.get_discord_user(uid=[str(value.id)])[0].owner().trainer()[0]
            except IndexError:
                return None
        elif isinstance(value, int):
            return self.client.get_user(account)[0].owner().trainer()[0]
        
    async def _get_emoji(self, ctx: discord.Context, emoji: str) -> str:
        if f'emoji_{emoji}' not in self.guild_defaults:
            raise ValueError
        
        if ctx.guild:
            return await getattr(self.config.guild(ctx.guild), f'emoji_{emoji}')()
        return self.guild_defaults.get(f'emoji_{emoji}')
    _e = _get_emoji
    
    class BaseCard(discord.Embed):
        def __init__(self, **kwargs) -> None:
            super().__init__(**kwargs)
            self.colour = kwargs.get('colour', kwargs.get('color', 13252437))
            
            self._author = {
                'name': 'TrainerDex',
                'url': 'https://www.trainerdex.co.uk/',
                'icon_url': 'https://www.trainerdex.co.uk/static/img/android-desktop.png',
            }
        
        async def build_card(self, parent, ctx: discord.Context) -> discord.Embed:
            self._parent = parent
            self._ctx = ctx
            
            self._footer = {
                'text': await self._parent.config.embed_footer()
            }
            
            notice = await self._parent.config.notice()
            if notice:
                emoji = await self._parent._e(self._ctx, 'notice')
                self._notice = f"{emoji} {notice}"
                
                if self.description:
                    self.description = "{}\n\n{}".format(self._notice, self.description)
                else:
                    self.description = self._notice
            return self
    
    async def _get_BaseCard(self, ctx: discord.Context, **kwargs) -> BaseCard:
        return await self.BaseCard(**kwargs).build_card(self, ctx)
    
    class ProfileCard(BaseCard):
        def __init__(self, trainer: trainerdex.Trainer, **kwargs):
            super().__init__(**kwargs)
            self._trainer = trainer
            self.colour = int(self._trainer.team().colour.replace("#", ""), 16)
            self.title = '{nickname} | TL{level}'.format(nickname=self._trainer.username, level=self._trainer.level.level)
            self.url = 'https://www.trainerdex.co.uk/profile?id={}'.format(self._trainer.id)
            if self._trainer.update:
                self.timestamp = self._trainer.update.update_time
        
        async def build_card(self, parent, ctx: discord.Context) -> discord.Embed:
            await super().build_card(parent, ctx)
            self.add_field(name='Team', value=self._trainer.team().name)
            self.add_field(name='Level', value=self._trainer.level.level)
            def check_xp(x):
                if x.xp is None:
                    return 0
                return x.xp
            self.add_field(name='Total XP', value="{:,}".format(max(self._trainer.updates(), key=check_xp).xp))
            return self
        
        async def add_guild_leaderboard(self) -> None:
            if self._ctx.guild:
                try:
                    guild_leaderboard = self._parent.client.get_discord_leaderboard(self._ctx.guild.id)
                except requests.exceptions.HTTPError as e:
                    log.error(e)
                else:
                    try:
                        guild_leaderboard = guild_leaderboard.filter_trainers([self._trainer.id])[0].position
                        self.insert_field_at(
                            index = 0,
                            name = '{guild} Leaderboard'.format(guild=self._ctx.guild.name),
                            value = str(guild_leaderboard),
                        )
                    except LookupError:
                        pass
        
        async def add_leaderboard(self) -> None:
            try:
                leaderboard = self._parent.client.get_worldwide_leaderboard()
            except requests.exceptions.HTTPError as e:
                log.error(e)
                return
            else:
                try:
                    leaderboard = leaderboard.filter_trainers([self._trainer.id])[0].position
                    self.insert_field_at(
                        index = 0,
                        name = 'Global Leaderboard',
                        value = str(leaderboard),
                    )
                except LookupError:
                    pass
    
    async def _get_ProfileCard(self, ctx: discord.Context, trainer: trainerdex.Trainer, **kwargs) -> ProfileCard:
        return await self.ProfileCard(trainer, **kwargs).build_card(self, ctx)
    
    @commands.group(name='profile')
    async def profile(self, ctx: discord.Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send('Hi!')
    
    @profile.command(name='lookup', aliases=["whois", "find"])
    async def profile__lookup(self, ctx: discord.Context, trainer: Union[discord.Member, str]) -> None:
        """Find a profile given a username."""
        
        async with ctx.typing():
            message = await ctx.send(f"{await self._e(ctx, 'loading')} Searching for profile...")
            
            trainer = await self.get_trainer(trainer)
            
            if trainer:
                await message.edit(content=f"{await self._e(ctx, 'loading')} Found profile. Loading...")
            else:
                await message.edit(content=f"{await self._e(ctx, 'failure')} Profile not found.")
                return
                
            embed = await self._get_ProfileCard(ctx, trainer)
            await message.edit(content=f"{await self._e(ctx, 'loading')} Checking leaderboard...", embed=embed)
            await embed.add_leaderboard()
            if ctx.guild:
                await message.edit(content=f"{await self._e(ctx, 'loading')} Checking {ctx.guild} leaderboard...", embed=embed)
                await embed.add_guild_leaderboard()
            await message.edit(content=None, embed=embed)
    
    @profile.command(name='create', alias=['register', 'approve', 'verify'])
    async def profile__create(self, ctx: discord.Context, mention: discord.Member, nickname: str = None, team: TeamConverter = None, total_xp: int = None) -> None:
        assign_roles = await self.config.guild(ctx.guild).assign_roles_on_join()
        set_nickname = await self.config.guild(ctx.guild).set_nickname_on_join()
        
        def message_in_channel_by_author(message: discord.Message):
            return message.author == ctx.author and message.channel == ctx.channel
        
        while nickname is None:
            await ctx.send(f"What is the in-game username of {mention}?")
            msg = await self.bot.wait_for('message', check=message_in_channel_by_author)
            nickname = msg.content
        
        while team is None:
            await ctx.send(f"What team is {nickname} in?")
            msg = await self.bot.wait_for('message', check=message_in_channel_by_author)
            team = await TeamConverter().convert(ctx, msg.content)
        
        while (total_xp is None) or (total_xp <= 100):
            await ctx.send(f"What is {nickname}'s Total XP?")
            msg = await self.bot.wait_for('message', check=message_in_channel_by_author)
            try:
                total_xp = int(msg.content.replace(',', '').replace('.', ''))
            except ValueError:
                await ctx.send(f"Please only enter the Total XP as a whole number")
        
        log.debug(f"Attempting to add {nickname} to database, checking if they already exist")
        
        progmessage = await ctx.send(f"{await self._e(ctx, 'loading')} Checking for user to database")
        
        trainer = None
        trainer = await self.get_trainer(nickname)
        if trainer is None:
            trainer = await self.get_trainer(mention)
        
        if trainer:
            log.debug("We found a trainer: {trainer.username}")
            await progmessage.edit(content=f"{await self._e(ctx, 'loading')} A record already exists in the database for this trainer.")
            def check_xp(x):
                if x.xp is None:
                    return 0
                return x.xp
            set_xp = (total_xp > max(trainer.updates(), key=check_xp).xp)
        else:
            log.debug("No Trainer Found, creating")
            await progmessage.edit(content=f"{await self._e(ctx, 'loading')} Creating {nickname}")
            user = self.client.create_user(username=username)
            discorduser = self.client.import_discord_user(uid=str(mention.id), user=user.id)
            trainer = self.client.create_trainer(username=nickname, team=team.id, account=user.id, verified=True)
            await progmessage.edit(content=f"{await self._e(ctx, 'success')} Created {trainer.username}.")
            set_xp = True
        
        if set_xp:
            await progmessage.edit(content=f"{await self._e(ctx, 'loading')} Setting Total XP for {trainer.username} to {total_xp}.")
            update = self.client.create_update(trainer, time_updated=ctx.message.created_at, xp=total_xp)
        await progmessage.edit(content=f"{await self._e(ctx, 'success')} Successfully added {mention.mention} as {trainer.username}.\n{await self._e(ctx, 'loading')} Loading profile...")
        trainer = self.client.get_trainer(trainer.id)
        embed = await self._get_ProfileCard(ctx, trainer)
        await progmessage.edit(embed=embed)
        
        embed = await self._get_ProfileCard(ctx, trainer)
        await progmessage.edit(content=f"{await self._e(ctx, 'success')} Successfully added {mention.mention} as {trainer.username}.\n{await self._e(ctx, 'loading')} Checking leaderboard...", embed=embed)
        await embed.add_leaderboard()
        await progmessage.edit(content=f"{await self._e(ctx, 'success')} Successfully added {mention.mention} as {trainer.username}.\n{await self._e(ctx, 'loading')} Checking {ctx.guild} leaderboard...", embed=embed)
        await embed.add_guild_leaderboard()
        await message.edit(content=f"{await self._e(ctx, 'success')} Successfully added {mention.mention} as {trainer.username}.", embed=embed)
