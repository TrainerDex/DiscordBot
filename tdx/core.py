import logging
import os
from typing import Union

import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.utils import chat_formatting

import trainerdex
from tdx.converters import DateConverter, TeamConverter
from tdx.embeds import BaseCard, ProfileCard, UpdatedProfileCard

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
    
    async def build_BaseCard(self, ctx: commands.Context, **kwargs) -> BaseCard:
        return await BaseCard(**kwargs).build_card(self, ctx)
    
    async def build_ProfileCard(self, ctx: commands.Context, trainer: trainerdex.Trainer, **kwargs) -> ProfileCard:
        return await ProfileCard(trainer, **kwargs).build_card(self, ctx)
    
    async def build_UpdatedProfileCard(self, ctx: commands.Context, trainer: trainerdex.Trainer, **kwargs) -> UpdatedProfileCard:
        return await UpdatedProfileCard(trainer, **kwargs).build_card(self, ctx)
    
    @commands.group(name='profile')
    async def profile(self, ctx: commands.Context) -> None:
        pass
    
    @profile.command(name='lookup', aliases=["whois", "find"])
    async def profile__lookup(self, ctx: commands.Context, trainer: Union[discord.User, discord.Member, str] = None) -> None:
        """Find a profile given a username."""
        
        async with ctx.typing():
            message = await ctx.send(loading("Searching for profile..."))
            
            if trainer is None:
                trainer = ctx.author
            trainer = await self.get_trainer(trainer)
            
            if trainer:
                await message.edit(content=loading("Found profile. Loading..."))
            else:
                await message.edit(content=chat_formatting.warning(" Profile not found."))
                return
                
            embed = await self.build_ProfileCard(ctx, trainer)
            await message.edit(content=loading("Checking leaderboard..."), embed=embed)
            await embed.add_leaderboard()
            if ctx.guild:
                await message.edit(content=loading(f"Checking {ctx.guild} leaderboard..."), embed=embed)
                await embed.add_guild_leaderboard()
            await message.edit(content=None, embed=embed)
    
    @profile.command(name='create', aliases=['register', 'approve', 'verify'])
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
        embed = await self.build_ProfileCard(ctx, trainer)
        await message.edit(embed=embed)
        
        embed = await self.build_ProfileCard(ctx, trainer)
        await message.edit(content=f"Successfully added {mention.mention} as {trainer.username}.\n"+loading("Checking leaderboard..."), embed=embed)
        await embed.add_leaderboard()
        await message.edit(content=f"Successfully added {mention.mention} as {trainer.username}.\n"+loading("Checking {ctx.guild} leaderboard..."), embed=embed)
        await embed.add_guild_leaderboard()
        await message.edit(content=f"Successfully added {mention.mention} as {trainer.username}.", embed=embed)
    
    @commands.command(name='progress')
    async def progress(self, ctx: commands.Context, trainer: Union[discord.User, discord.Member, str] = None) -> None:
        """Find a profile given a username."""
        
        async with ctx.typing():
            message = await ctx.send(loading("Searching for profile..."))
            
            print(trainer, type(trainer))
            if trainer is None:
                trainer = ctx.author
                print(trainer, type(trainer))
            trainer = await self.get_trainer(trainer)
            
            if trainer:
                await message.edit(content=loading("Found profile. Loading..."))
            else:
                await message.edit(content=chat_formatting.warning(" Profile not found."))
                return
                
            embed = await self.build_UpdatedProfileCard(ctx, trainer)
            await message.edit(content=loading("Checking leaderboard..."), embed=embed)
            await embed.add_leaderboard()
            if ctx.guild:
                await message.edit(content=loading(f"Checking {ctx.guild} leaderboard..."), embed=embed)
                await embed.add_guild_leaderboard()
            await message.edit(content=None, embed=embed)
