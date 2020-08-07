import logging
import os
from typing import Final, Optional

import discord
from redbot.core import checks, commands, Config
from redbot.core.bot import Red
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf, menus, predicates

import PogoOCR
from tdx import converters, client
from tdx.embeds import BaseCard, ProfileCard
from tdx.utils import check_xp, append_twitter, loading, success, QuestionMessage

log: logging.Logger = logging.getLogger(__name__)
POGOOCR_TOKEN_PATH: Final = os.path.join(os.path.dirname(__file__), "data/key.json")
_ = Translator("TrainerDex", __file__)


class TrainerDex(commands.Cog):
    """TrainerDex Core Functionality"""

    def __init__(self, bot: Red, config: Config) -> None:
        self.bot: Red = bot
        self.config: Config = config
        self.client = None
        self.PREV_EMOJI = self.bot.get_emoji(729769958652772505)
        self.NEXT_EMOJI = self.bot.get_emoji(729770058099982347)

        assert os.path.isfile(POGOOCR_TOKEN_PATH)  # Looks for a Google Cloud Token

    async def initialize(self) -> None:
        await self._create_client()

    async def _create_client(self) -> None:
        """Create TrainerDex API Client"""
        token = await self._get_token()
        self.client = client.Client(token=token)

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

        await source_message.add_reaction(self.bot.get_emoji(471298325904359434))

        trainer: client.Trainer = await converters.TrainerConverter().convert(
            None, source_message.author, cli=self.client
        )
        if not trainer:
            await source_message.remove_reaction(
                self.bot.get_emoji(471298325904359434), self.bot.user
            )
            await source_message.add_reaction("\N{THUMBS DOWN SIGN}\N{VARIATION SELECTOR-16}")
            await source_message.channel.send(
                "{message.author.mention} Trainer not found!", delete_after=5
            )
            return

        async with source_message.channel.typing():
            try:
                message: discord.Message = await source_message.channel.send(
                    loading(_("That's a nice image you have there, let's see…"))
                )
                ocr = PogoOCR.ProfileSelf(
                    POGOOCR_TOKEN_PATH, image_uri=source_message.attachments[0].proxy_url
                )
                ocr.get_text()

                data_found = {
                    "travel_km": ocr.travel_km,
                    "capture_total": ocr.capture_total,
                    "pokestops_visited": ocr.pokestops_visited,
                    "total_xp": ocr.total_xp,
                }

                if data_found.get("total_xp"):
                    await message.edit(
                        content=append_twitter(
                            loading(
                                _(
                                    "{user}, we found the following stats:\n"
                                    "{stats}\nJust processing that now…"
                                )
                            ).format(user=source_message.author.mention, stats=cf.box(data_found))
                        )
                    )

                    if max(trainer.updates, key=check_xp).total_xp > data_found.get("total_xp"):
                        await message.edit(
                            content=append_twitter(
                                cf.warning(
                                    _(
                                        "You've previously set your XP to higher than what you're trying to set it to. "
                                        "It's currently set to {xp}."
                                    )
                                )
                            ).format(xp=cf.humanize_number(data_found.get("total_xp")))
                        )
                        await source_message.remove_reaction(
                            self.bot.get_emoji(471298325904359434), self.bot.user
                        )
                        await source_message.add_reaction(
                            "\N{WARNING SIGN}\N{VARIATION SELECTOR-16}"
                        )
                        return
                    elif max(trainer.updates, key=check_xp).total_xp == data_found.get("total_xp"):
                        text: str = cf.warning(
                            _(
                                "You've already set your XP to this figure. "
                                "In future, to see the output again, please run the `progress` command as it costs us to run OCR."
                            )
                        )
                        await source_message.remove_reaction(
                            self.bot.get_emoji(471298325904359434), self.bot.user
                        )
                        await source_message.add_reaction(
                            "\N{WARNING SIGN}\N{VARIATION SELECTOR-16}"
                        )
                    else:
                        await trainer.post(
                            stats=data_found,
                            data_source="ss_ocr",
                            update_time=source_message.created_at,
                        )
                        await source_message.remove_reaction(
                            self.bot.get_emoji(471298325904359434), self.bot.user
                        )
                        await source_message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
                        text = None

                    await message.edit(
                        content="\n".join(
                            [x for x in [text, loading(_("Loading output…"))] if x is not None]
                        )
                    )
                    embed: discord.Embed = await ProfileCard(source_message, trainer)
                    await message.edit(content=text, embed=embed)
                else:
                    await message.edit(
                        content=cf.error(_("I could not find Total XP in your image. "))
                        + "\n\n"
                        + cf.info(
                            _(
                                "We use Google Vision API to read your images. "
                                "Please ensure that the ‘Total XP’ field is visible. "
                                "If it is visible and your image still doesn't scan after a minute, try a new image. "
                                "Posting the same image again, will likely cause another failure."
                            )
                        )
                    )
                    await source_message.remove_reaction(
                        self.bot.get_emoji(471298325904359434), self.bot.user
                    )
                    await source_message.add_reaction(
                        "\N{THUMBS DOWN SIGN}\N{VARIATION SELECTOR-16}"
                    )
            except Exception as e:
                await source_message.channel.send(
                    "`Error in function 'check_screenshot'. Check your console or logs for details.`"
                    + "\n\n"
                    + cf.info(
                        _(
                            "We use Google Vision API to read your images. "
                            "Please ensure that the ‘Total XP’ field is visible. "
                            "If it is visible and your image still doesn't scan after a minute, try a new image. "
                            "Posting the same image again, will likely cause another failure."
                        )
                    )
                )
                raise e

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

        message = await ctx.send(
            loading(_("{tag} Downloading global leaderboard…")).format(tag=ctx.author.mention)
        )
        leaderboard = await self.client.get_leaderboard()
        await message.edit(
            content=loading(_("{tag} Processing results!")).format(tag=ctx.author.mention)
        )
        embeds = []
        working_embed = BASE_EMBED.copy()

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
                working_embed = BASE_EMBED.copy()
        if len(working_embed.fields) > 0:
            embeds.append(working_embed)
        await message.edit(
            content=_(
                "{tag}: React ❌ to close the leaderboard. Navigate by reacting {prev} or {next}."
            ).format(tag=ctx.author.mention, prev=self.PREV_EMOJI, next=self.NEXT_EMOJI)
        )
        await ctx.message.delete()

        if ctx.channel.permissions_for(ctx.me).external_emojis:
            menu_controls = (
                {
                    self.PREV_EMOJI: menus.prev_page,
                    "❌": menus.close_menu,
                    self.NEXT_EMOJI: menus.next_page,
                }
                if len(embeds) > 1
                else {"❌": menus.close_menu}
            )
        else:
            menu_controls = menus.DEFAULT_CONTROLS if len(embeds) > 1 else {"❌": menus.close_menu}

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
            message: discord.Message = await ctx.send(loading(_("Searching for profile…")))

            if trainer is None:
                trainer: client.Trainer = await converters.TrainerConverter().convert(
                    ctx, ctx.author, cli=self.client
                )

            if trainer:
                await message.edit(content=loading(_("Found profile. Loading…")))
            else:
                await message.edit(content=cf.warning(_("Profile not found.")))
                return

            embed: discord.Embed = await ProfileCard(ctx, trainer)
            await message.edit(content=loading(_("Checking progress…")), embed=embed)
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

        If `guild.assign_roles_on_join` or `guild.set_nickname_on_join` are True, it will do those actions before checking the database.

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

            team: client.Faction = await converters.safe_convert(
                converters.TeamConverter, ctx, q.answer
            )
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
                _("What is {nickname}‘s Total XP? (as a whole number)").format(nickname=nickname),
                check=predicates.MessagePredicate.valid_int(ctx),
            )
            await q.ask(self.bot)
            if q.exit:
                return await q.response.add_reaction("\N{WHITE HEAVY CHECK MARK}")

            total_xp = q.answer
            answer_text: str = cf.humanize_number(total_xp)
            await q.message.edit(content=f"{q.message.content}\n{answer_text}")

        message: discord.Message = await ctx.send(loading(_("Let's go…")))

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
                            roles=cf.humanize_list([str(x) for x in roles["add"]]),
                            user=mention.mention,
                        )
                    )

                    try:
                        await mention.add_roles(
                            *roles["add"],
                            reason=_("{mod} ran the command `{command}`").format(
                                mod=ctx.author, command=ctx.invoked_with
                            ),
                        )
                    except (discord.errors.Forbidden, discord.errors.HTTPException) as e:
                        roles_added = False
                        roles_added_error = e
                    else:
                        await message.edit(
                            content=success(_("Added roles ({roles}) to {user}")).format(
                                roles=cf.humanize_list([str(x) for x in roles["add"]]),
                                user=mention.mention,
                            )
                        )
                        roles_added = len(roles["add"])

                roles["remove"] = [ctx.guild.get_role(x) for x in roles["remove"]]
                if roles["remove"]:
                    await message.edit(
                        content=loading(_("Removing roles ({roles}) from {user}")).format(
                            roles=cf.humanize_list([str(x) for x in roles["remove"]]),
                            user=mention.mention,
                        )
                    )

                    try:
                        await mention.remove_roles(
                            *roles["remove"],
                            reason=_("{mod} ran the command `{command}`").format(
                                mod=ctx.author, command=ctx.invoked_with
                            ),
                        )
                    except (discord.errors.Forbidden, discord.errors.HTTPException) as e:
                        roles_removed = False
                        roles_removed_error = e
                    else:
                        await message.edit(
                            content=success(_("Removed roles ({roles}) from {user}")).format(
                                roles=cf.humanize_list([str(x) for x in roles["remove"]]),
                                user=mention.mention,
                            )
                        )
                        roles_removed = len(roles["remove"])

        if set_nickname:
            async with ctx.typing():
                await message.edit(
                    content=loading(_("Changing {user}‘s nick to {nickname}")).format(
                        user=mention.mention, nickname=nickname
                    )
                )

                try:
                    await mention.edit(
                        nick=nickname,
                        reason=_("{mod} ran the command `{command}`").format(
                            mod=ctx.author, command=ctx.invoked_with
                        ),
                    )
                except (discord.errors.Forbidden, discord.errors.HTTPException) as e:
                    nick_set = False
                    nick_set_error = e
                else:
                    await message.edit(
                        content=success(_("Changed {user}‘s nick to {nickname}")).format(
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

        log.info(f"Attempting to add {nickname} to database, checking if they already exist")

        await message.edit(content=loading(_("Checking for user to database")))

        try:
            trainer: client.Trainer = await converters.TrainerConverter().convert(
                ctx, nickname, cli=self.client
            )
        except commands.BadArgument:
            try:
                trainer: client.Trainer = await converters.TrainerConverter().convert(
                    ctx, mention, cli=self.client
                )
            except commands.BadArgument:
                trainer = None

        if trainer is not None:
            log.info("We found a trainer: {trainer.username}")
            await message.edit(
                content=loading(
                    _("An existing record was found for {user}. Updating details…").format(
                        user=trainer.username
                    )
                )
            )

            # Edit the trainer instance with the new team and set is_verified
            # Chances are, is_verified might have been False and this will fix that.
            await trainer.edit(faction=team.id, is_verified=True)

            # Check if it's a good idea to update the stats
            set_xp = (
                (total_xp > max(trainer.updates, key=check_xp).total_xp)
                if trainer.updates
                else True
            )
        else:
            log.info(f"{nickname}: No user found, creating profile")
            await message.edit(content=loading(_("Creating {user}")).format(user=nickname))
            trainer: client.Trainer = await self.client.create_trainer(
                username=nickname, faction=team.id, is_verified=True
            )
            user = await trainer.user()
            await user.add_discord(mention)
            await message.edit(content=loading(_("Created {user}")).format(user=nickname))
            set_xp: bool = True

        if set_xp:
            await message.edit(
                content=loading(_("Setting Total XP for {user} to {total_xp}.")).format(
                    user=trainer.username, total_xp=total_xp,
                )
            )
            await trainer.post(
                stats={"total_xp": total_xp()},
                data_source="ss_ocr",
                update_time=ctx.message.created_at,
            )
        await message.edit(
            content=(
                success(_("Successfully added {user} as {trainer}."))
                + "\n"
                + loading(_("Loading profile…"))
            ).format(
                user=mention.mention, trainer=trainer.username,
            )
        )
        embed: discord.Embed = await ProfileCard(ctx, trainer)
        await message.edit(
            content=success(_("Successfully added {user} as {trainer}.")).format(
                user=mention.mention, trainer=trainer.username,
            ),
            embed=embed,
        )
