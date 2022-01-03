import json
import logging
import os
import PogoOCR
from contextlib import suppress
from discord.errors import DiscordException, Forbidden, HTTPException
from discord.ext.alternatives import silent_delete
from discord.ext.commands.errors import BadArgument
from discord.member import Member
from discord.message import Message
from discord.role import Role
from redbot.core import checks, commands
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf
from redbot.core.utils import predicates
from trainerdex.faction import Faction
from trainerdex.trainer import Trainer
from trainerdex.user import User
from trainerdex.update import Update
from typing import Any, Callable, Dict, Final, List, Literal, Optional, TypedDict, Union

from . import converters
from .abc import MixinMeta
from .datatypes import StoredRoles, TransformedRoles
from .embeds import ProfileCard
from .utils import (
    AbandonQuestionException,
    NoAnswerProvidedException,
    Question,
    introduction_notes,
    loading,
    success,
)

logger: logging.Logger = logging.getLogger(__name__)
_: Translator = Translator("TrainerDex", __file__)

POGOOCR_TOKEN_PATH: Final[str] = os.path.join(os.path.dirname(__file__), "data/key.json")


class ModCmds(MixinMeta):
    async def ask_question(
        self,
        ctx: commands.Context,
        question: str,
        optional: bool = False,
        predicate: Optional[Callable] = None,
        converter: Optional[commands.Converter] = None,
    ) -> Union[str, Any]:
        m: Message = await ctx.send(content=self.emoji.get("loading"))
        attempts_remaining: int = 5

        while attempts_remaining > 0:
            attempts_remaining -= 1
            q: Question = Question(ctx, question, message=m, predicate=predicate)

            try:
                answer: str = await q.ask()
            except AbandonQuestionException as e:
                raise AbandonQuestionException(e)

            await q.append_answer(answer)
            await q.response.delete(silent=True)

            if converter:
                try:
                    answer: Any = await converter().convert(ctx, answer)
                except commands.BadArgument as e:
                    await ctx.send(content=e, delete_after=30.0)
                    continue
                else:
                    await q.append_answer(answer)

            return answer
        else:
            raise NoAnswerProvidedException

    @commands.command(name="approve", aliases=["ap", "register", "verify"])
    @checks.mod_or_permissions(manage_roles=True)
    async def approve_trainer(
        self,
        ctx: commands.Context,
        member: Member,
        nickname: Optional[converters.NicknameConverter] = None,
        team: Optional[converters.TeamConverter] = None,
        total_xp: Optional[converters.TotalXPConverter] = None,
    ) -> None:
        """Create a profile in TrainerDex

        If `guild.assign_roles_on_join` or `guild.set_nickname_on_join` are True, it will do those actions before checking the database.

        If a trainer already exists for this profile, it will update the Total XP is needed.

        The command may ask you a few questions. To exit out, say `[p]cancel`.

        """
        assign_roles: bool = await self.config.guild(ctx.guild).assign_roles_on_join()
        set_nickname: bool = await self.config.guild(ctx.guild).set_nickname_on_join()

        class QuestionType(TypedDict):
            question: str
            converter: commands.Converter
            predicate: Optional[predicates.MessagePredicate]

        questions: Dict[str, QuestionType] = {
            "nickname": {
                "question": _("What is the in-game username of {user}?").format(user=member),
                "converter": converters.NicknameConverter,
            },
            "team": {
                "question": _("What team is {user} in?").format(user=member),
                "converter": converters.TeamConverter,
            },
            "total_xp": {
                "question": _("What is {user}‘s Total XP?").format(user=member),
                "predicate": predicates.MessagePredicate.valid_int(ctx),
                "converter": converters.TotalXPConverter,
            },
        }

        class AnswersFormats(TypedDict):
            nickname: str
            team: Faction
            total_xp: int

        answers: AnswersFormats = {
            "nickname": nickname,
            "team": team,
            "total_xp": total_xp,
        }

        for key, values in questions.items():
            if answers.get(key) is None:
                try:
                    answers[key] = await self.ask_question(ctx, **values)
                except NoAnswerProvidedException:
                    await ctx.send(_("Answer could not be determined. Abandoning!"))
                    return
                except AbandonQuestionException:
                    await ctx.send(_("Cancelled!"))
                    return

        message: Message = await ctx.send(loading(_("Let's go…")))

        if assign_roles:
            async with ctx.typing():

                stored_roles: StoredRoles = await self.config.guild(
                    ctx.guild
                ).roles_to_assign_on_approval()

                # Transform stored roles to a list of roles
                roles: TransformedRoles = {
                    key: [ctx.guild.get_role(role_id) for role_id in stored_roles[key]]
                    for key in stored_roles
                }

                if answers["team"].id > 0:
                    team_role: int = await getattr(
                        self.config.guild(ctx.guild),
                        ["", "mystic_role", "valor_role", "instinct_role"][answers["team"].id],
                    )()
                    if team_role:
                        roles["add"].append(ctx.guild.get_role(team_role))

                if roles["add"]:
                    await message.edit(
                        content=loading(_("Adding roles ({roles}) to {user}")).format(
                            roles=cf.humanize_list([str(x) for x in roles["add"]]),
                            user=member.mention,
                        )
                    )

                    try:
                        await member.add_roles(
                            *roles["add"],
                            reason=_("{mod} ran the command `{command}`").format(
                                mod=ctx.author, command=ctx.invoked_with
                            ),
                        )
                    except (Forbidden, HTTPException) as e:
                        roles_added: bool = False
                        roles_added_error: DiscordException = e
                    else:
                        await message.edit(
                            content=success(_("Added roles ({roles}) to {user}")).format(
                                roles=cf.humanize_list([str(x) for x in roles["add"]]),
                                user=member.mention,
                            )
                        )
                        roles_added: int = len(roles["add"])

                if roles["remove"]:
                    await message.edit(
                        content=loading(_("Removing roles ({roles}) from {user}")).format(
                            roles=cf.humanize_list([str(x) for x in roles["remove"]]),
                            user=member.mention,
                        )
                    )

                    try:
                        await member.remove_roles(
                            *roles["remove"],
                            reason=_("{mod} ran the command `{command}`").format(
                                mod=ctx.author, command=ctx.invoked_with
                            ),
                        )
                    except (Forbidden, HTTPException) as e:
                        roles_removed: bool = False
                        roles_removed_error: DiscordException = e
                    else:
                        await message.edit(
                            content=success(_("Removed roles ({roles}) from {user}")).format(
                                roles=cf.humanize_list([str(x) for x in roles["remove"]]),
                                user=member.mention,
                            )
                        )
                        roles_removed: int = len(roles["remove"])

        if set_nickname:
            async with ctx.typing():
                await message.edit(
                    content=loading(_("Changing {user}‘s nick to {nickname}")).format(
                        user=member.mention, nickname=answers.get("nickname")
                    )
                )

                try:
                    await member.edit(
                        nick=answers.get("nickname"),
                        reason=_("{mod} ran the command `{command}`").format(
                            mod=ctx.author, command=ctx.invoked_with
                        ),
                    )
                except (Forbidden, HTTPException) as e:
                    nick_set: bool = False
                    nick_set_error: DiscordException = e
                else:
                    await message.edit(
                        content=success(_("Changed {user}‘s nick to {nickname}")).format(
                            user=member.mention, nickname=answers.get("nickname")
                        )
                    )
                    nick_set: bool = True

        async with ctx.typing():
            if assign_roles or set_nickname:
                approval_message: str = success(_("{user} has been approved!\n")).format(
                    user=member.mention
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
                    ).format(nickname=answers.get("nickname"))
                    approval_message += f"`{nick_set_error}`\n"

            if assign_roles or set_nickname:
                await message.edit(content=approval_message)
                message: Message = await ctx.send(loading(""))

        logger.info(
            "Attempting to add %(user)s to database, checking if they already exist",
            {"user": answers.get("nickname")},
        )

        await message.edit(content=loading(_("Checking for user in database")))

        try:
            trainer: Trainer = await converters.TrainerConverter().convert(
                ctx, answers.get("nickname"), cli=self.client
            )
        except commands.BadArgument:
            try:
                trainer: Trainer = await converters.TrainerConverter().convert(
                    ctx, member, cli=self.client
                )
            except commands.BadArgument:
                trainer = None

        if trainer is not None:
            logger.info("We found a trainer: %(trainer)s", {"trainer": trainer.username})
            await message.edit(
                content=loading(
                    _("An existing record was found for {user}. Updating details…").format(
                        user=trainer.username
                    )
                )
            )

            # Edit the trainer instance with the new team and set is_verified
            # Chances are, is_verified might have been False and this will fix that.
            await trainer.edit(faction=answers.get("team").id, is_verified=True)

            # Check if it's a good idea to update the stats
            await trainer.fetch_updates()
            latest_update_with_total_xp: Update = trainer.get_latest_update_for_stat("total_xp")
            set_xp: bool = (
                (answers.get("total_xp") > latest_update_with_total_xp.total_xp)
                if trainer.updates
                else True
            )
        else:
            logger.info("%s: No user found, creating profile", nickname)
            await message.edit(content=loading(_("Creating {user}")).format(user=nickname))
            trainer: Trainer = await self.client.create_trainer(
                username=nickname, faction=answers.get("team").id, is_verified=True
            )
            user: User = await trainer.user()
            await user.add_discord(member)
            await message.edit(content=loading(_("Created {user}")).format(user=nickname))
            set_xp: bool = True

        if set_xp:
            await message.edit(
                content=loading(_("Setting Total XP for {user} to {total_xp}.")).format(
                    user=trainer.username,
                    total_xp=answers.get("total_xp"),
                )
            )
            await trainer.post(
                stats={"total_xp": answers.get("total_xp")},
                data_source="ss_ocr",
                update_time=ctx.message.created_at,
            )
        else:
            await message.edit(
                content=loading(_("Won't set Total XP for {user}.")).format(user=trainer.username)
            )

        custom_message: str = await self.config.guild(ctx.guild).introduction_note()
        notes: str = introduction_notes(ctx, member, trainer, additional_message=custom_message)

        with suppress(Forbidden):
            await member.send(notes[0])
            if len(notes) == 2:
                await member.send(notes[1])
        await message.edit(
            content=(
                success(_("Successfully added {user} as {trainer}."))
                + "\n"
                + loading(_("Loading profile…"))
            ).format(
                user=member.mention,
                trainer=trainer.username,
            )
        )
        embed: ProfileCard = await ProfileCard(
            ctx=ctx, bot=self.bot, client=self.client, trainer=trainer, emoji=self.emoji
        )
        with suppress(Forbidden):
            await member.send(embed=embed)
        await message.edit(
            content=success(_("Successfully added {user} as {trainer}.")).format(
                user=member.mention,
                trainer=trainer.username,
            ),
            embed=embed,
        )

    @commands.group(name="tdxmod", case_insensitive=True)
    async def tdxmod(self, ctx: commands.Context) -> None:
        """⬎ TrainerDex-specific Moderation Commands"""
        pass

    @tdxmod.command(name="debug")
    @checks.mod()
    async def tdxmod__debug(self, ctx: commands.Context, message: Message) -> None:
        """Returns a reason why OCR would have failed"""
        original_context: commands.Context = await self.bot.get_context(message)
        async with ctx.channel.typing():
            if await self.bot.cog_disabled_in_guild(self, original_context.guild):
                await ctx.send(
                    _(
                        "Message {message.id} failed because the cog is disabled in the guild"
                    ).format(message)
                )
                return

            if len(original_context.message.attachments) == 0:
                await ctx.send(
                    _("Message {message.id} failed because there is no file attached.").format(
                        message=message
                    )
                )
                return

            if len(original_context.message.attachments) > 1:
                await ctx.send(
                    _("Message {message.id} failed because there more than file attached.").format(
                        message=message
                    )
                )
                return

            if os.path.splitext(original_context.message.attachments[0].proxy_url)[
                1
            ].lower() not in [
                ".jpeg",
                ".jpg",
                ".png",
            ]:
                await ctx.send(
                    _("Message {message.id} failed because the file is not jpg or png.").format(
                        message=message
                    )
                )
                return

            profile_ocr: bool = await self.config.channel(original_context.channel).profile_ocr()
            if not profile_ocr:
                await ctx.send(
                    _(
                        "Message {message.id} failed because that channel is not enabled for OCR"
                    ).format(message=message)
                )
                return

            try:
                await converters.TrainerConverter().convert(
                    original_context, original_context.author, cli=self.client
                )
            except BadArgument:
                await ctx.send(
                    _(
                        "Message {message.id} failed because I couldn't find a TrainerDex user for {message.author}"
                    ).format(message=message)
                )
                return

            try:
                ocr: PogoOCR.ProfileSelf = PogoOCR.ProfileSelf(
                    POGOOCR_TOKEN_PATH, image_uri=original_context.message.attachments[0].proxy_url
                )
                ocr.get_text()
            except Exception as e:
                message: Message = await ctx.send(
                    _("Message {message.id} failed because for an unknown reason").format(
                        message=message
                    )
                )
                await ctx.send(cf.box(e))
                message_content: str = str(ocr.text_found[0].description)
                if len(message_content) <= 1994:
                    await ctx.send(cf.box(message_content))
                else:
                    await message.edit(
                        file=cf.text_to_file(
                            message_content, filename=f"full_debug_{message.id}.txt"
                        )
                    )
                return
            else:
                message_content: str = str(ocr.text_found[0].description)
                data_found: Dict[str, Any] = {
                    "locale": ocr.locale,
                    "numeric_locale": ocr.numeric_locale,
                    "username": ocr.username,
                    "buddy_name": ocr.buddy_name,
                    "travel_km": ocr.travel_km,
                    "capture_total": ocr.capture_total,
                    "pokestops_visited": ocr.pokestops_visited,
                    "total_xp": ocr.total_xp,
                    "start_date": ocr.start_date,
                }
                if len(message_content) <= 1994:
                    await ctx.send(cf.box(message_content))
                else:
                    await ctx.send(
                        file=cf.text_to_file(message_content, filename=f"debug_{message.id}.txt")
                    )

                try:
                    data_found_jsonish_string: str = json.dumps(data_found, default=repr)
                except (TypeError, OverflowError, TypeError):
                    data_found_jsonish_string: str = str(data_found)

                data_found_string_format: Literal["json", "py"] = (
                    "json" if isinstance(data_found_jsonish_string, str) else "py"
                )

                formatted_output: str = cf.box(
                    data_found_jsonish_string,
                    lang=data_found_string_format,
                )

                if len(formatted_output) <= 2000:
                    await ctx.send(formatted_output)
                else:
                    await ctx.send(
                        file=cf.text_to_file(
                            data_found_jsonish_string,
                            filename=f"debug_{message.id}.{data_found_string_format}",
                        )
                    )
                return

    @tdxmod.command(name="auto-role")
    @checks.mod_or_permissions(manage_roles=True)
    async def autorole(self, ctx: commands.Context) -> None:
        """EXPERIMENTAL: Checks for existing users that don't have the right roles, and applies them

        Warning: This command is slow and experimental. I wouldn't recommend running it without checking by your roles_to_assign_on_approval setting first.
        It can really mess with roles on a mass scale.
        """
        assign_roles: bool = await self.config.guild(ctx.guild).assign_roles_on_join()
        if assign_roles is False:
            return
        set_nickname: bool = await self.config.guild(ctx.guild).set_nickname_on_join()
        roles: StoredRoles = await self.config.guild(ctx.guild).roles_to_assign_on_approval()
        add_roles: List[Role] = [ctx.guild.get_role(x) for x in roles["add"]]
        del_roles: List[Role] = [ctx.guild.get_role(x) for x in roles["remove"]]
        team_roles: List[Union[None, Role]] = [
            None,
            ctx.guild.get_role(await self.config.guild(ctx.guild).mystic_role()),
            ctx.guild.get_role(await self.config.guild(ctx.guild).valor_role()),
            ctx.guild.get_role(await self.config.guild(ctx.guild).instinct_role()),
        ]
        members: List[Member] = [x for x in ctx.guild.members if not x.bot]

        members_to_edit: List[Member] = []
        await ctx.send("Starting ({}/{})".format(len(set(members_to_edit)), len(members)))
        for role in add_roles:
            message: Message = await ctx.send(
                "Checking {} ({}/{})".format(role, len(set(members_to_edit)), len(members))
            )
            members_to_edit += [m for m in members if role not in m.roles]
            await message.edit(
                content="Checked `{}` ({}/{})".format(
                    role, len(set(members_to_edit)), len(members)
                )
            )
        for role in del_roles:
            message: Message = await ctx.send(
                "Checking {} ({}/{})".format(role, len(set(members_to_edit)), len(members))
            )
            members_to_edit += [m for m in members if role in m.roles]
            await message.edit(
                content="Checked `{}` ({}/{})".format(
                    role, len(set(members_to_edit)), len(members)
                )
            )
        members_to_edit = list(set(members_to_edit))

        members_approved: int = 0
        message: Message = await ctx.send(
            "{} approved, {} checked, {} total".format(members_approved, 0, len(members_to_edit))
        )
        async with ctx.typing():
            for index, member in enumerate(members_to_edit):
                try:
                    trainer: Trainer = await converters.TrainerConverter().convert(
                        ctx, member, cli=self.client
                    )
                except commands.BadArgument:
                    await message.edit(
                        content="{} approved, {} checked, {} total".format(
                            members_approved, index + 1, len(members_to_edit)
                        )
                    )
                    continue
                if trainer.is_verified:
                    roles_to_add: List[Role] = list(set(add_roles))
                    if trainer.faction > 0:
                        roles_to_add.append(team_roles[trainer.faction])
                    if roles_to_add:
                        try:
                            await member.add_roles(
                                *roles_to_add,
                                reason=_("{mod} ran the command `{command}`").format(
                                    mod=ctx.author, command=ctx.invoked_with
                                ),
                            )
                        except (Forbidden, HTTPException):
                            pass

                    if del_roles:
                        try:
                            await member.remove_roles(
                                *del_roles,
                                reason=_("{mod} ran the command `{command}`").format(
                                    mod=ctx.author, command=ctx.invoked_with
                                ),
                            )
                        except (Forbidden, HTTPException):
                            pass

                    if set_nickname:
                        try:
                            await member.edit(
                                nick=trainer.nickname,
                                reason=_("{mod} ran the command `{command}`").format(
                                    mod=ctx.author, command=ctx.invoked_with
                                ),
                            )
                        except (Forbidden, HTTPException):
                            pass
                    members_approved += 1
                await message.edit(
                    content="{} approved, {} checked, {} total".format(
                        members_approved, index + 1, len(members_to_edit)
                    )
                )
