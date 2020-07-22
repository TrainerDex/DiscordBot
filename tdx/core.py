import datetime
import json
import logging
import os
import requests
from typing import Union, List

import discord
from redbot.core import checks, commands, Config
from redbot.core.bot import Red
from redbot.core.utils import chat_formatting

import trainerdex
from tdx.converters import DateConverter, TeamConverter

log = logging.getLogger("red.tdx.core")
POGOOCR_TOKEN_PATH = os.path.join(os.path.dirname(__file__), 'data/key.json')


def loading(text: str) -> str:
    """Get text prefixed with an loading emoji.
    
    Returns
    -------
    str
    The new message.
    
    """
    return "<a:loading:471298325904359434> {}".format(text)

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
            'assign_roles_on_join': True,
            'set_nickname_on_join': True,
            'set_nickname_on_update': True,
            'roles_to_assign_on_approval': {'add': [], 'remove': []},
            'mystic_role': None,
            'valor_role': None,
            'instinct_role': None,
            'tl40_role': None,
        }
        self.channel_defaults = {
            'profile_ocr': False,
            'notices': False,
            'post_leaderboard': False,
        }
        
        self.config.register_global(**self.global_defaults)
        self.config.register_guild(**self.guild_defaults)
        self.config.register_channel(**self.channel_defaults)
    
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
    
    async def get_trainer(self, value: Union[discord.Member, discord.User, str, int] = None) -> trainerdex.Trainer:
        if isinstance(value, str):
            return self.client.get_trainer_from_username(value)
        elif isinstance(value, (discord.Member, discord.User)):
            try:
                return self.client.get_discord_user(uid=[str(value.id)])[0].owner().trainer()[0]
            except IndexError:
                return None
        elif isinstance(value, int):
            return self.client.get_user(value)[0].owner().trainer()[0]
    
    class BaseCard(discord.Embed):
        def __init__(self, **kwargs) -> None:
            super().__init__(**kwargs)
            self.colour = kwargs.get('colour', kwargs.get('color', 13252437))
            
            self._author = {
                'name': 'TrainerDex',
                'url': 'https://www.trainerdex.co.uk/',
                'icon_url': 'https://www.trainerdex.co.uk/static/img/android-desktop.png',
            }
        
        async def build_card(self, parent, ctx: commands.Context) -> discord.Embed:
            self._parent = parent
            self._ctx = ctx
            
            self._footer = {
                'text': await self._parent.config.embed_footer()
            }
            
            notice = await self._parent.config.notice()
            if notice:
                notice = chat_formatting.info(notice)
                
                if self.description:
                    self.description = "{}\n\n{}".format(notice, self.description)
                else:
                    self.description = notice
            return self
    
    async def _get_BaseCard(self, ctx: commands.Context, **kwargs) -> BaseCard:
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
        
        async def build_card(self, parent, ctx: commands.Context) -> discord.Embed:
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
    
    async def _get_ProfileCard(self, ctx: commands.Context, trainer: trainerdex.Trainer, **kwargs) -> ProfileCard:
        return await self.ProfileCard(trainer, **kwargs).build_card(self, ctx)
    
    @commands.group(name='profile')
    async def profile(self, ctx: commands.Context) -> None:
        pass
    
    @profile.command(name='lookup', aliases=["whois", "find"])
    async def profile__lookup(self, ctx: commands.Context, trainer: Union[discord.Member, str]) -> None:
        """Find a profile given a username."""
        
        async with ctx.typing():
            message = await ctx.send(loading("Searching for profile..."))
            
            trainer = await self.get_trainer(trainer)
            
            if trainer:
                await message.edit(content=loading("Found profile. Loading..."))
            else:
                await message.edit(content=chat_formatting.warning(" Profile not found."))
                return
                
            embed = await self._get_ProfileCard(ctx, trainer)
            await message.edit(content=loading("Checking leaderboard..."), embed=embed)
            await embed.add_leaderboard()
            if ctx.guild:
                await message.edit(content=loading(f"Checking {ctx.guild} leaderboard..."), embed=embed)
                await embed.add_guild_leaderboard()
            await message.edit(content=None, embed=embed)
    
    @profile.command(name='create', alias=['register', 'approve', 'verify'])
    async def profile__create(self, ctx: commands.Context, mention: discord.Member, nickname: str = None, team: TeamConverter = None, total_xp: int = None) -> None:
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
        
        
        message = await ctx.send(loading("Let's go..."))
        
        member_edit_dict = {}
        
        if assign_roles:
            async with ctx.typing():
                roles_to_add_on_join=[ctx.guild.get_role(x) for x in await self.config.guild(ctx.guild).roles_to_assign_on_approval()['add']]
                roles_to_remove_on_join=[ctx.guild.get_role(x) for x in await self.config.guild(ctx.guild).roles_to_assign_on_approval()['remove']]
                member_edit_dict['roles'] = [x for x in (roles_to_add_on_join+mention.roles) if x not in roles_to_remove_on_join]
        
        if set_nickname:
            async with ctx.typing():
                member_edit_dict['nick'] = nickname
        
        async with ctx.typing():
            if member_edit_dict:
                await message.edit(content=loading(f"Setting {chat_formatting.humanize_list(member_edit_dict.keys())} for user {mention.mention}..."))
                try:
                    await mention.edit(reason="Approval via TrainerDex", **member_edit_dict)
                except discord.errors.Forbidden as e:
                    await message.edit(content=chat_formatting.error(f"{mention.mention}: {chat_formatting.humanize_list(member_edit_dict.keys())} could not be set.\n`{e}`"))
                else:
                    await message.edit(content=f"{mention.mention} has been approved! {chat_formatting.humanize_list(member_edit_dict.keys())} has been set.")
                message = await ctx.send(loading(''))
        
        
        
        
        log.debug(f"Attempting to add {nickname} to database, checking if they already exist")
        
        await message.edit(content=loading("Checking for user to database"))
        
        trainer = None
        trainer = await self.get_trainer(nickname)
        if trainer is None:
            trainer = await self.get_trainer(mention)
        
        if trainer:
            log.debug("We found a trainer: {trainer.username}")
            await message.edit(content=loading("A record already exists in the database for this trainer."))
            def check_xp(x):
                if x.xp is None:
                    return 0
                return x.xp
            set_xp = (total_xp > max(trainer.updates(), key=check_xp).xp)
        else:
            log.debug("No Trainer Found, creating")
            await message.edit(content=loading(f"Creating {nickname}"))
            user = self.client.create_user(username=nickname)
            discorduser = self.client.import_discord_user(uid=str(mention.id), user=user.id)
            trainer = self.client.create_trainer(username=nickname, team=team.id, account=user.id, verified=True)
            await message.edit(content=f"Created {trainer.username}")
            set_xp = True
        
        if set_xp:
            await message.edit(content=loading(f"Setting Total XP for {trainer.username} to {total_xp}."))
            update = self.client.create_update(trainer, time_updated=ctx.message.created_at, xp=total_xp)
        await message.edit(content=f"Successfully added {mention.mention} as {trainer.username}.\n"+loading("Loading profile..."))
        trainer = self.client.get_trainer(trainer.id)
        embed = await self._get_ProfileCard(ctx, trainer)
        await message.edit(embed=embed)
        
        embed = await self._get_ProfileCard(ctx, trainer)
        await message.edit(content=f"Successfully added {mention.mention} as {trainer.username}.\n"+loading("Checking leaderboard..."), embed=embed)
        await embed.add_leaderboard()
        await message.edit(content=f"Successfully added {mention.mention} as {trainer.username}.\n"+loading("Checking {ctx.guild} leaderboard..."), embed=embed)
        await embed.add_guild_leaderboard()
        await message.edit(content=f"Successfully added {mention.mention} as {trainer.username}.", embed=embed)
    
    @commands.group(name='tdxset', alias=['config'])
    async def settings(self, ctx: commands.Context) -> None:
        pass
    
    @settings.group(name='guild', alias=['server'])
    async def settings__guild(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            settings = await self.config.guild(ctx.guild).all()
            settings = json.dumps(settings, indent=2, ensure_ascii=False)
            await ctx.send(chat_formatting.box(settings, 'json'))
    
    @settings__guild.command(name='assign_roles_on_join')
    async def settings__guild__assign_roles_on_join(self, ctx: commands.Context, value: bool = None) -> None:
        """Modify the roles of members when they're approved.
        
        This is useful for granting users access to the rest of the server.
        """
        if value:
            await self.config.guild(ctx.guild).assign_roles_on_join.set(value)
            await ctx.tick()
            await ctx.send(f"`guild.assign_roles_on_join` set to {value}")
        else:
            await ctx.send_help()
            value = await self.config.guild(ctx.guild).assign_roles_on_join()
            await ctx.send(f"`guild.assign_roles_on_join` is {value}")
        
    @settings__guild.command(name='set_nickname_on_join')
    async def settings__guild__set_nickname_on_join(self, ctx: commands.Context, value: bool = None) -> None:
        """Modify the nickname of members when they're approved.
        
        This is useful for ensuring players can be easily identified.
        """
        if value:
            await self.config.guild(ctx.guild).set_nickname_on_join.set(value)
            await ctx.tick()
            await ctx.send(f"`guild.set_nickname_on_join` set to {value}")
        else:
            await ctx.send_help()
            value = await self.config.guild(ctx.guild).set_nickname_on_join()
            await ctx.send(f"`guild.set_nickname_on_join` is {value}")
        
    @settings__guild.command(name='set_nickname_on_update')
    async def settings__guild__set_nickname_on_update(self, ctx: commands.Context, value: bool = None) -> None:
        """Modify the nickname of members when they update their Total XP.
        
        This is useful for setting levels in their name.
        """
        if value:
            await self.config.guild(ctx.guild).set_nickname_on_update.set(value)
            await ctx.tick()
            await ctx.send(f"`guild.set_nickname_on_update` set to {value}")
        else:
            await ctx.send_help()
            value = await self.config.guild(ctx.guild).set_nickname_on_update()
            await ctx.send(f"`guild.set_nickname_on_update` is {value}")
        
    @settings__guild.command(name='roles_to_assign_on_approval')
    async def settings__guild__roles_to_assign_on_approval(self, ctx: commands.Context, action: str = None, roles: discord.Role = None) -> None:
        """Which roles to add/remove to a user on approval
        
        Usage:
            [p]tdxset guild roles_to_assign_on_approval add @Verified, @Trainer ...
                Assign these roles to users when they are approved
            [p]tdxset guild roles_to_assign_on_approval remove @Guest
                Remove these roles from users when they are approved
        """
        roles_to_assign_on_approval = await self.config.guild(ctx.guild).roles_to_assign_on_approval()
        if action == 'add':
            if roles:
                roles_to_assign_on_approval['add'] = [x.id for x in ctx.message.role_mentions]
                await self.config.guild(ctx.guild).roles_to_assign_on_approval.set(roles_to_assign_on_approval)
                await ctx.tick()
                value = await self.config.guild(ctx.guild).roles_to_assign_on_approval()
                value = json.dumps(value, indent=2, ensure_ascii=False)
                await ctx.send(chat_formatting.box(value, 'json'))
        elif action == 'remove':
            if roles:
                roles_to_assign_on_approval['remove'] = [x.id for x in ctx.message.role_mentions]
                await self.config.guild(ctx.guild).set_nickname_on_update.set(roles_to_assign_on_approval)
                await ctx.tick()
                value = await self.config.guild(ctx.guild).roles_to_assign_on_approval()
                value = json.dumps(value, indent=2, ensure_ascii=False)
                await ctx.send(chat_formatting.box(value, 'json'))
        else:
            await ctx.send_help()
            value = await self.config.guild(ctx.guild).roles_to_assign_on_approval()
            value = json.dumps(value, indent=2, ensure_ascii=False)
            await ctx.send(chat_formatting.box(value, 'json'))
        
    @settings__guild.command(name='mystic_role')
    async def settings__guild__mystic_role(self, ctx: commands.Context, value: discord.Role = None) -> None:
        if value:
            await self.config.guild(ctx.guild).mystic_role.set(value.id)
            await ctx.tick()
            await ctx.send(f"`guild.mystic_role` set to {value}")
        else:
            await ctx.send_help()
            value = await self.config.guild(ctx.guild).mystic_role()
            await ctx.send(f"`guild.mystic_role` is {ctx.guild.get_role(value)}")
        
    @settings__guild.command(name='valor_role')
    async def settings__guild__valor_role(self, ctx: commands.Context, value: discord.Role = None) -> None:
        if value:
            await self.config.guild(ctx.guild).valor_role.set(value.id)
            await ctx.tick()
            await ctx.send(f"`guild.valor_role` set to {value}")
        else:
            await ctx.send_help()
            value = await self.config.guild(ctx.guild).valor_role()
            await ctx.send(f"`guild.valor_role` is {ctx.guild.get_role(value)}")
        
    @settings__guild.command(name='instinct_role')
    async def settings__guild__instinct_role(self, ctx: commands.Context, value: discord.Role = None) -> None:
        if value:
            await self.config.guild(ctx.guild).instinct_role.set(value.id)
            await ctx.tick()
            await ctx.send(f"`guild.instinct_role` set to {value}")
        else:
            await ctx.send_help()
            value = await self.config.guild(ctx.guild).instinct_role()
            await ctx.send(f"`guild.instinct_role` is {ctx.guild.get_role(value)}")
        
    @settings__guild.command(name='tl40_role')
    async def settings__guild__tl40_role(self, ctx: commands.Context, value: discord.Role = None) -> None:
        if value:
            await self.config.guild(ctx.guild).tl40_role.set(value.id)
            await ctx.tick()
            await ctx.send(f"`guild.tl40_role` set to {value}")
        else:
            await ctx.send_help()
            value = await self.config.guild(ctx.guild).tl40_role()
            await ctx.send(f"`guild.tl40_role` is {ctx.guild.get_role(value)}")
