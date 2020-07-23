import logging
import os
from typing import Union

import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf

import trainerdex
import PogoOCR
from tdx.converters import TeamConverter
from tdx.embeds import BaseCard, ProfileCard, UpdatedProfileCard
from  tdx.utils import check_xp, contact_us_on_twitter

log = logging.getLogger("red.tdx.core")
POGOOCR_TOKEN_PATH = os.path.join(os.path.dirname(__file__), 'data/key.json')
_ = Translator("TrainerDex", __file__)


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
    
    def __init__(self, bot: Red, config: Config) -> None:
        self.bot = bot
        self.config = config
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
            return self.client.get_trainer(value)
    
    async def build_BaseCard(self, ctx: commands.Context, **kwargs) -> BaseCard:
        return await BaseCard(**kwargs).build_card(self, ctx)
    
    async def build_ProfileCard(self, ctx: commands.Context, trainer: trainerdex.Trainer, **kwargs) -> ProfileCard:
        return await ProfileCard(trainer, **kwargs).build_card(self, ctx)
    
    async def build_UpdatedProfileCard(self, ctx: commands.Context, trainer: trainerdex.Trainer, **kwargs) -> UpdatedProfileCard:
        return await UpdatedProfileCard(trainer, **kwargs).build_card(self, ctx)
    
    @commands.Cog.listener('on_message')
    async def check_screenshot(self, source_message: discord.Message) -> None:
        if source_message.author.bot:
            return
        
        profile_ocr = await self.config.channel_from_id(source_message.channel.id).profile_ocr()
        if not profile_ocr:
            return
        
        if len(source_message.attachments) != 1:
            return
        
        trainer = await self.get_trainer(source_message.author)
        if not trainer:
            return
        
        async with source_message.channel.typing():
            message = await source_message.channel.send(loading(_("That's a nice image you have there, let's see..."))+"\n"+cf.info(_("Please refrain from posting non-profile images in this channel. If your image doesn't scan, please try a new image. Image processing isn't free.")))
            ocr = PogoOCR.ProfileSelf(POGOOCR_TOKEN_PATH, image_uri=source_message.attachments[0].proxy_url)
            ocr.get_text()
            if ocr.total_xp:
                text = loading(_("{user}, we're sure your XP is {xp}. Just processing that now...")).format(
                    user=source_message.author.mention,
                    xp=ocr.total_xp,
                )
                await message.edit(content=text+'\n\n'+contact_us_on_twitter())
                if max(trainer.updates(), key=check_xp).xp > ocr.total_xp:
                    await message.edit(content=cf.warning((_("You've previously set your XP to higher than what you're trying to set it to. It's currently set to {xp}."))+'\n\n'+contact_us_on_twitter()).format(xp=cf.humanize_number(ocr.total_xp)))
                    return
                elif max(trainer.updates(), key=check_xp).xp == ocr.total_xp:
                    text = cf.warning(_("You've already set your XP to this figure. In future, to see the output again, please run the `progress` command as it costs us to run OCR."))
                else:
                    update = self.client.create_update(trainer.id, ocr.total_xp)
                    text = _("✅ Success")
                    trainer = await self.get_trainer(trainer.id)
                
                await message.edit(content=text + '\n' + loading(_("Loading output...")))
                embed = await self.build_UpdatedProfileCard(source_message, trainer)
                await message.edit(content=text, embed=embed)
                return
    
    @commands.group(name='profile')
    async def profile(self, ctx: commands.Context) -> None:
        pass
    
    @profile.command(name='lookup', aliases=["whois", "find"])
    async def profile__lookup(self, ctx: commands.Context, trainer: Union[discord.User, discord.Member, str] = None) -> None:
        """Find a profile given a username."""
        
        async with ctx.typing():
            message = await ctx.send(loading(_("Searching for profile...")))
            
            if trainer is None:
                trainer = ctx.author
            trainer = await self.get_trainer(trainer)
            
            if trainer:
                await message.edit(content=loading(_("Found profile. Loading...")))
            else:
                await message.edit(content=cf.warning(_("Profile not found.")))
                return
                
            embed = await self.build_ProfileCard(ctx, trainer)
            await message.edit(content=loading(_("Checking leaderboard...")), embed=embed)
            await embed.add_leaderboard()
            if ctx.guild:
                await message.edit(content=loading(_("Checking {guild} leaderboard...").format(guild=ctx.guild)), embed=embed)
                await embed.add_guild_leaderboard()
            await message.edit(content=None, embed=embed)
    
    @profile.command(name='create', aliases=['register', 'approve', 'verify'])
    async def profile__create(self, ctx: commands.Context, mention: discord.Member, nickname: str = None, team: TeamConverter = None, total_xp: int = None) -> None:
        assign_roles = await self.config.guild(ctx.guild).assign_roles_on_join()
        set_nickname = await self.config.guild(ctx.guild).set_nickname_on_join()
        
        def message_in_channel_by_author(message: discord.Message):
            return message.author == ctx.author and message.channel == ctx.channel
        
        while nickname is None:
            await ctx.send(cf.question(_("What is the in-game username of {mention}?")).format(mention=mention))
            msg = await self.bot.wait_for('message', check=message_in_channel_by_author)
            nickname = msg.content
        
        while team is None:
            await ctx.send(cf.question(_("What team is {nickname} in?")).format(nickname=nickname))
            msg = await self.bot.wait_for('message', check=message_in_channel_by_author)
            team = await TeamConverter().convert(ctx, msg.content)
        
        while (total_xp is None) or (total_xp <= 100):
            await ctx.send(cf.question(_("What is {nickname}'s Total XP?")).format(nickname=nickname))
            msg = await self.bot.wait_for('message', check=message_in_channel_by_author)
            try:
                total_xp = int(msg.content.replace(',', '').replace('.', ''))
            except ValueError:
                await ctx.send(_("Please only enter the Total XP as a whole number"))
        
        
        message = await ctx.send(loading(_("Let's go...")))
        
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
                await message.edit(content=loading(_("Setting {roles_and_or_nick} for {user}")).format(
                    roles_and_or_nick=cf.humanize_list(member_edit_dict.keys()),
                    user=mention.mention,
                ))
                try:
                    await mention.edit(reason=_("Approval via TrainerDex"), **member_edit_dict)
                except discord.errors.Forbidden as e:
                    await message.edit(content=cf.error(
                        mention.mention+ \
                        ": "+ \
                        _("{roles_and_or_nick} could not be set.")+ \
                        "\n{e}"
                    ).format(
                        roles_and_or_nick=cf.humanize_list(member_edit_dict.keys()),
                        e=e,
                    ))
                else:
                    await message.edit(content=_("{user} has been approved! {roles_and_or_nick} had been set.").format(
                        user=mention.mention,
                        roles_and_or_nick=cf.humanize_list(member_edit_dict.keys()),
                    ))
                message = await ctx.send(loading(''))
        
        log.debug(f"Attempting to add {nickname} to database, checking if they already exist")
        
        await message.edit(content=loading(_("Checking for user to database")))
        
        trainer = None
        trainer = await self.get_trainer(nickname)
        if trainer is None:
            trainer = await self.get_trainer(mention)
        
        if trainer:
            log.debug("We found a trainer: {trainer.username}")
            await message.edit(content=loading(_("A record already exists in the database for this trainer.")))
            set_xp = (total_xp > max(trainer.updates(), key=check_xp).xp)
        else:
            log.debug("No Trainer Found, creating")
            await message.edit(content=loading(_("Creating {user}")).format(user=nickname))
            user = self.client.create_user(username=nickname)
            discorduser = self.client.import_discord_user(uid=str(mention.id), user=user.id)
            trainer = self.client.create_trainer(username=nickname, team=team.id, account=user.id, verified=True)
            await message.edit(content=loading(_("Created {user}")).format(user=nickname))
            set_xp = True
        
        if set_xp:
            await message.edit(content=loading(_("Setting Total XP for {user} to {total_xp}.")).format(
                user=trainer.username,
                total_xp=total_xp,
            ))
            update = self.client.create_update(trainer, time_updated=ctx.message.created_at, xp=total_xp)
        await message.edit(content=(
            _("Successfully added {user} as {trainer}.")+ \
            "\n"+ \
            loading(_("Loading profile..."))
        ).format(
            user=mention.mention,
            trainer=trainer.username,
        ))
        trainer = self.client.get_trainer(trainer.id)
        embed = await self.build_ProfileCard(ctx, trainer)
        await message.edit(content=(
            _("Successfully added {user} as {trainer}.")+ \
            "\n"+ \
            loading(_("Checking leaderboard..."))
        ).format(
            user=mention.mention,
            trainer=trainer.username,
        ), embed=embed)
        await embed.add_leaderboard()
        await message.edit(content=(
            _("Successfully added {user} as {trainer}.")+ \
            "\n"+ \
            loading(_("Checking {guild} leaderboard..."))
        ).format(
            user=mention.mention,
            trainer=trainer.username,
            guild=ctx.guild,
        ), embed=embed)
        await embed.add_guild_leaderboard()
        await message.edit(content=_("Successfully added {user} as {trainer}.").format(
            user=mention.mention,
            trainer=trainer.username,
        ), embed=embed)
    
    @commands.command(name='progress')
    async def progress(self, ctx: commands.Context, trainer: Union[discord.User, discord.Member, str] = None) -> None:
        """Find a profile given a username."""
        
        async with ctx.typing():
            message = await ctx.send(loading(_("Searching for profile...")))
            
            print(trainer, type(trainer))
            if trainer is None:
                trainer = ctx.author
                print(trainer, type(trainer))
            trainer = await self.get_trainer(trainer)
            
            if trainer:
                await message.edit(content=loading(_("Found profile. Loading...")))
            else:
                await message.edit(content=cf.warning(_("Profile not found.")))
                return
                
            embed = await self.build_UpdatedProfileCard(ctx, trainer)
            await message.edit(content=loading(_("Checking leaderboard...")), embed=embed)
            await embed.add_leaderboard()
            if ctx.guild:
                await message.edit(content=loading(_("Checking {guild} leaderboard...").format(guild=ctx.guild)), embed=embed)
                await embed.add_guild_leaderboard()
            await message.edit(content=None, embed=embed)
