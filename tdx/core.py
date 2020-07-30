import logging
import os
from itertools import islice, takewhile, repeat
from typing import Dict, Final, List, Optional, Union

import discord
from redbot.core import checks, commands, Config
from redbot.core.bot import Red
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf, menus, predicates

import trainerdex
import PogoOCR
from tdx import converters
from tdx.embeds import BaseCard, ProfileCard
from tdx.models import Faction
from tdx.leaderboard import Leaderboard
from tdx.utils import check_xp, contact_us_on_twitter, QuestionMessage

log: logging.Logger = logging.getLogger("red.tdx.core")
POGOOCR_TOKEN_PATH: Final = os.path.join(os.path.dirname(__file__), "data/key.json")
_ = Translator("TrainerDex", __file__)


def loading(text: str) -> str:
    """Get text prefixed with a loading emoji if the bot has access to it.
    
    Returns
    -------
    str
    The new message.
    
    """

    emoji = "<a:loading:471298325904359434>"
    return f"{emoji} {text}"


def success(text: str) -> str:
    """Get text prefixed with a white checkmark.
    
    Returns
    -------
    str
    The new message.
    
    """
    emoji = "\N{WHITE HEAVY CHECK MARK}"
    return f"{emoji} {text}"


class TrainerDex(commands.Cog):
    """TrainerDex Core Functionality"""

    def __init__(self, bot: Red, config: Config) -> None:
        self.bot: Red = bot
        self.config: Config = config
        self.client: Optional[trainerdex.Client] = None
        self.PREV_EMOJI = self.bot.get_emoji(729769958652772505)
        self.NEXT_EMOJI = self.bot.get_emoji(729770058099982347)

        assert os.path.isfile(POGOOCR_TOKEN_PATH)  # Looks for a Google Cloud Token

    async def initialize(self) -> None:
        await self._create_client()

    async def _create_client(self) -> None:
        """Create TrainerDex API Client"""
        token = await self._get_token()
        self.client = trainerdex.Client(token=token, identifier="ts_social_discord")

    async def _get_token(self) -> str:
        """Get TrainerDex token"""
        api_tokens = await self.bot.get_shared_api_tokens("trainerdex")
        token = api_tokens.get("token", "")
        if not token:
            log.warning("No valid token found")
        return token

    @commands.Cog.listener("on_message")
    async def check_screenshot(self, source_message: discord.Message) -> None:
        if source_message.author.bot:
            return

        profile_ocr: bool = await self.config.channel_from_id(
            source_message.channel.id
        ).profile_ocr()
        if not profile_ocr:
            return

        if len(source_message.attachments) != 1:
            return

        trainer: trainerdex.Trainer = await converters.TrainerConverter().convert(
            None, source_message.author
        )
        if not trainer:
            await source_message.channel.send(
                "{message.author.mention} Trainer not found!", delete_after=5
            )
            return

        async with source_message.channel.typing():
            message: discord.Message = await source_message.channel.send(
                loading(_("That's a nice image you have there, let's see..."))
                + "\n"
                + cf.info(
                    _(
                        "Please refrain from posting non-profile images in this channel. If your image doesn't scan, please try a new image. Image processing isn't free."
                    )
                )
            )
            ocr = PogoOCR.ProfileSelf(
                POGOOCR_TOKEN_PATH, image_uri=source_message.attachments[0].proxy_url
            )
            ocr.get_text()
            if ocr.total_xp:
                text: str = loading(
                    _("{user}, we're sure your XP is {xp}. Just processing that now...")
                ).format(
                    user=source_message.author.mention, xp=ocr.total_xp,
                )
                await message.edit(content=text + "\n\n" + contact_us_on_twitter())
                if max(trainer.updates(), key=check_xp).xp > ocr.total_xp:
                    await message.edit(
                        content=cf.warning(
                            (
                                _(
                                    "You've previously set your XP to higher than what you're trying to set it to. It's currently set to {xp}."
                                )
                            )
                            + "\n\n"
                            + contact_us_on_twitter()
                        ).format(xp=cf.humanize_number(ocr.total_xp))
                    )
                    return
                elif max(trainer.updates(), key=check_xp).xp == ocr.total_xp:
                    text: str = cf.warning(
                        _(
                            "You've already set your XP to this figure. In future, to see the output again, please run the `progress` command as it costs us to run OCR."
                        )
                    )
                else:
                    update: trainerdex.Update = self.client.create_update(trainer.id, ocr.total_xp)
                    text: str = _("✅ Success")
                    trainer: trainerdex.Trainer = self.client.get_trainer(trainer.id)

                await message.edit(content=text + "\n" + loading(_("Loading output...")))
                embed: discord.Embed = await ProfileCard(source_message, trainer)
                await message.edit(content=text, embed=embed)
                return

    @commands.group(name="profile")
    async def profile(self, ctx: commands.Context) -> None:
        pass

    @commands.command(name="leaderboard", aliases=["lb"])
    async def leaderboard(self, ctx: commands.Context, limit: int = 100) -> None:
        """Limited to top 100 results by default, but can be overiden
        
        Example:
            `[p]leaderboard`
            Returns 100 results
            
            `[p]leaderboard 250`
            Returns 250 results
        """

        BASE_EMBED = await BaseCard(ctx, title=_("Global Leaderboard"))
        PAGE_LEN = 15

        await ctx.tick()

        if ctx.channel.permissions_for(ctx.me).external_emojis:
            menu_controls = (
                {
                    self.PREV_EMOJI: menus.prev_page,
                    "❌": menus.close_menu,
                    self.NEXT_EMOJI: menus.next_page,
                }
                if len(results) > 1
                else {"❌": menus.close_menu}
            )
        else:
            menu_controls = menu.DEFAULT_CONTROLS if len(results) > 1 else {"❌": menus.close_menu}

        message = await ctx.send(
            loading(_("{tag} Downloading global leaderboard...")).format(tag=ctx.author.mention)
        )
        leaderboard = await Leaderboard(limit=limit)
        await message.edit(
            content=loading(_("{tag} Processing results!")).format(tag=ctx.author.mention)
        )
        embeds = []
        working_embed = base_embed.copy()

        async for entry in leaderboard:
            """If embed at field limit, append to embeds list and start a fresh embed"""
            if len(working_embed.fields) < PAGE_LEN:
                working_embed.add_field(
                    name="{} {}".format(entry.position, entry.username),
                    value=cf.humanize_number(entry.total_xp),
                    inline=False,
                )
            if len(working_embed.fields) == PAGE_LEN:
                embeds.append(working_embed)
                await message.edit(
                    content=loading(_("{tag} Processing results ({pages} pages)")).format(
                        tag=ctx.author.mention, pages=len(embeds)
                    )
                )
                working_embed = base_embed.copy()
        if len(working_embed.fields) > 0:
            embeds.append(working_embed)
        await message.edit(
            content=_(
                "{tag}: React ❌ to close the leaderboard. Navigate by reacting {prev} or {next}."
            ).format(tag=ctx.author.mention, prev=self.PREV_EMOJI, next=self.NEXT_EMOJI)
        )
        await ctx.message.delete()

        menus.start_adding_reactions(message, menu_controls.keys())
        await menus.menu(
            ctx, embeds, menu_controls, message=message,
        )

    @profile.command(name="lookup", aliases=["whois", "find", "progress", "trainer"])
    async def profile__lookup(
        self, ctx: commands.Context, trainer: converters.TrainerConverter = None,
    ) -> None:
        """Find a profile given a username."""

        async with ctx.typing():
            message: discord.Message = await ctx.send(loading(_("Searching for profile...")))

            if trainer is None:
                trainer: trainerdex.Trainer = await converters.TrainerConverter().convert(
                    ctx, ctx.author
                )

            if trainer:
                await message.edit(content=loading(_("Found profile. Loading...")))
            else:
                await message.edit(content=cf.warning(_("Profile not found.")))
                return

            embed: discord.Embed = await ProfileCard(ctx, trainer)
            await message.edit(content=loading(_("Checking progress...")), embed=embed)
            await embed.show_progress()
            await message.edit(content=None, embed=embed)

    @profile.command(name="create", aliases=["register", "approve", "verify"])
    @checks.mod_or_permissions(manage_roles=True)
    async def profile__create(
        self,
        ctx: commands.Context,
        mention: discord.Member,
        nickname: Optional[converters.NicknameConverter] = None,
        team: Optional[converters.TeamConverter] = None,
        total_xp: Optional[int] = None,
    ) -> None:
        """Get or create a profile in TrainerDex
        
        If `guild.assign_roles_on_join` and/or `guild.set_nickname_on_join` are True, it will do those actions before checking the database.
        
        If a trainer already exists for this profile, it will update the Total XP is needed.
        
        The command may ask you a few questions. To exit out, say `[p]cancel`.
        
        """
        assign_roles: bool = await self.config.guild(ctx.guild).assign_roles_on_join()
        set_nickname: bool = await self.config.guild(ctx.guild).set_nickname_on_join()

        while nickname is None:
            q = QuestionMessage(
                ctx, _("What is the in-game username of {mention}?").format(mention=mention)
            )
            await q.ask(self.bot)
            if q.exit:
                return await q.response.add_reaction("\N{WHITE HEAVY CHECK MARK}")

            nickname: str = await converters.safe_convert(
                converters.NicknameConverter, ctx, q.answer
            )
            if nickname:
                answer_text: str = nickname
                await q.message.edit(content=f"{q.message.content}\n{answer_text}")
            else:
                await ctx.send(nickname.e)
                nickname = None

        while team is None:
            q = QuestionMessage(ctx, _("What team is {nickname} in?").format(nickname=nickname))
            await q.ask(self.bot)
            if q.exit:
                return await q.response.add_reaction("\N{WHITE HEAVY CHECK MARK}")

            team: Faction = await converters.safe_convert(converters.TeamConverter, ctx, q.answer)
            if team:
                answer_text: str = team
                await q.message.edit(content=f"{q.message.content}\n{answer_text}")
            else:
                await ctx.send(team.e)
                team = None

        MINIMUM_XP_CAP = 100
        while (total_xp is None) or (total_xp <= MINIMUM_XP_CAP):
            q = QuestionMessage(
                ctx,
                _("What is {nickname}'s Total XP? (as a whole number)").format(nickname=nickname),
                check=predicates.MessagePredicate.valid_int(ctx),
            )
            await q.ask(self.bot)
            if q.exit:
                return await q.response.add_reaction("\N{WHITE HEAVY CHECK MARK}")

            total_xp = q.result
            answer_text: str = cf.humanize_number(total_xp)
            await q.message.edit(content=f"{q.message.content}\n{answer_text}")

        message: discord.Message = await ctx.send(loading(_("Let's go...")))

        member_edit_dict: Dict = {}

        if assign_roles:
            async with ctx.typing():
                roles = await self.config.guild(ctx.guild).roles_to_assign_on_approval()
                roles["add"] = [ctx.guild.get_role(x) for x in roles["add"]]
                if team.id > 0:
                    team_role = await getattr(
                        self.config.guild(ctx.guild),
                        ["", "mystic_role", "valor_role", "instinct_role"][team.id],
                    )()
                    if team_role:
                        roles["add"].append(ctx.guild.get_role(team_role))

                if roles["add"]:
                    await message.edit(
                        content=loading(_("Adding roles ({roles}) to {user}")).format(
                            roles=cf.humanize_list(roles["add"]), user=mention.mention,
                        )
                    )

                    try:
                        mention.add_roles(roles["add"], reason=_("Approval via TrainerDex"))
                    except (discord.errors.Forbidden, discord.errors.HTTPException) as e:
                        roles_added = False
                        roles_added_error = e
                    else:
                        await message.edit(
                            content=success(_("Added roles ({roles}) to {user}")).format(
                                roles=cf.humanize_list(roles["add"]), user=mention.mention,
                            )
                        )
                        roles_added = len(roles["add"])

                roles["remove"] = [ctx.guild.get_role(x) for x in roles["remove"]]
                if roles["remove"]:
                    await message.edit(
                        content=loading(_("Removing roles ({roles}) from {user}")).format(
                            roles=cf.humanize_list(roles["remove"]), user=mention.mention,
                        )
                    )

                    try:
                        mention.remove_roles(roles["remove"], reason=_("Approval via TrainerDex"))
                    except (discord.errors.Forbidden, discord.errors.HTTPException) as e:
                        roles_removed = False
                        roles_removed_error = e
                    else:
                        await message.edit(
                            content=success(_("Removed roles ({roles}) from {user}")).format(
                                roles=cf.humanize_list(roles["remove"]), user=mention.mention,
                            )
                        )
                        roles_removed = len(roles["remove"])

        if set_nickname:
            async with ctx.typing():
                await message.edit(
                    content=loading(_("Changing {user}'s nick to {nickname}")).format(
                        user=mention.mention, nickname=nickname
                    )
                )

                try:
                    await mention.edit(nick=nickname)
                except (discord.errors.Forbidden, discord.errors.HTTPException) as e:
                    nick_set = False
                    nick_set_error = e
                else:
                    await message.edit(
                        content=success(_("Changed {user}'s nick to {nickname}")).format(
                            user=mention.mention, nickname=nickname
                        )
                    )
                    nick_set = True

        async with ctx.typing():
            if assign_roles or set_nickname:
                approval_message = success(_("{user} has been approved!\n")).format(
                    user=mention.mention
                )

            if assign_roles:
                if roles["add"]:
                    if roles_added:
                        approval_message += success(_("{count} role(s) added.\n")).format(
                            count=roles_added
                        )
                    else:
                        approval_message += cf.error(
                            _("Some roles could not be added. ({roles})\n")
                        ).format(roles=cf.humanize_list(roles["add"]))
                        approval_message += f"`{roles_added_error}`\n"

                if roles["remove"]:
                    if roles_removed:
                        approval_message += success(_("{count} role(s) removed.\n")).format(
                            count=roles_removed
                        )
                    else:
                        approval_message += cf.error(
                            _("Some roles could not be removed. ({roles})\n")
                        ).format(roles=cf.humanize_list(roles["remove"]))
                        approval_message += f"`{roles_removed_error}`\n"

            if set_nickname:
                if nick_set:
                    approval_message += success(_("User nickname set.\n"))
                else:
                    approval_message += cf.error(
                        _("User nickname could not be set. (`{nickname}`)\n")
                    ).format(nickname=nickname)
                    approval_message += f"`{nick_set_error}`\n"

            if assign_roles or set_nickname:
                await message.edit(content=approval_message)
                message: discord.Message = await ctx.send(loading(""))

        log.debug(f"Attempting to add {nickname} to database, checking if they already exist")

        await message.edit(content=loading(_("Checking for user to database")))

        try:
            trainer: Optional[trainerdex.Trainer] = await converters.TrainerConverter().convert(
                ctx, nickname
            )
        except commands.BadArgument:
            try:
                trainer: Optional[
                    trainerdex.Trainer
                ] = await converters.TrainerConverter().convert(ctx, mention)
            except commands.BadArgument:
                trainer = None

        if trainer:
            log.debug("We found a trainer: {trainer.username}")
            await message.edit(
                content=loading(_("A record already exists in the database for this trainer."))
            )
            set_xp: bool = total_xp > max(trainer.updates(), key=check_xp).xp
        else:
            log.debug("No Trainer Found, creating")
            await message.edit(content=loading(_("Creating {user}")).format(user=nickname))
            user: trainerdex.User = self.client.create_user(username=nickname)
            discorduser: trainerdex.DiscordUser = self.client.import_discord_user(
                uid=str(mention.id), user=user.id
            )
            trainer: trainerdex.Trainer = self.client.create_trainer(
                username=nickname, team=team.id, account=user.id, verified=True
            )
            await message.edit(content=loading(_("Created {user}")).format(user=nickname))
            set_xp: bool = True

        if set_xp:
            await message.edit(
                content=loading(_("Setting Total XP for {user} to {total_xp}.")).format(
                    user=trainer.username, total_xp=total_xp,
                )
            )
            update: trainerdex.Update = self.client.create_update(
                trainer, time_updated=ctx.message.created_at, xp=total_xp
            )
        await message.edit(
            content=(
                success(_("Successfully added {user} as {trainer}."))
                + "\n"
                + loading(_("Loading profile..."))
            ).format(
                user=mention.mention, trainer=trainer.username,
            )
        )
        trainer: trainerdex.Trainer = self.client.get_trainer(trainer.id)
        embed: discord.Embed = await ProfileCard(ctx, trainer)
        await message.edit(
            content=success(_("Successfully added {user} as {trainer}.")).format(
                user=mention.mention, trainer=trainer.username,
            ),
            embed=embed,
        )
