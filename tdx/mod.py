import json
import logging
import os
from typing import Final, Callable, Optional

import discord
from discord.ext.alternatives import silent_delete
from redbot.core import checks, commands
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf, predicates

import trainerdex as client
import PogoOCR
from . import converters
from .abc import MixinMeta
from .embeds import ProfileCard
from .utils import (
    AbandonQuestionException,
    check_xp,
    introduction_notes,
    loading,
    NoAnswerProvidedException,
    Question,
    success,
)

log: logging.Logger = logging.getLogger(__name__)
_ = Translator("TrainerDex", __file__)
POGOOCR_TOKEN_PATH: Final = os.path.join(os.path.dirname(__file__), "data/key.json")


class ModCmds(MixinMeta):
    async def ask_question(
        self,
        ctx: commands.Context,
        question: str,
        optional: bool = False,
        predicate: Optional[Callable] = None,
        converter: commands.Converter = None,
    ):
        m = await ctx.send(content=self.emoji.get("loading"))
        attempts_remaining = 5

        while attempts_remaining > 0:
            attempts_remaining -= 1
            q = Question(ctx, question, message=m, predicate=predicate)

            try:
                answer = await q.ask()
            except AbandonQuestionException as e:
                raise AbandonQuestionException(e)

            await q.append_answer(answer)
            await q.response.delete(silent=True)

            if converter:
                try:
                    answer = await converter().convert(ctx, answer)
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
        member: discord.Member,
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

        questions = {
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
        answers = {
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

        message: discord.Message = await ctx.send(loading(_("Let's go…")))

        if assign_roles:
            async with ctx.typing():
                roles = await self.config.guild(ctx.guild).roles_to_assign_on_approval()
                roles["add"] = [ctx.guild.get_role(x) for x in roles["add"]]
                if answers.get("team").id > 0:
                    team_role = await getattr(
                        self.config.guild(ctx.guild),
                        ["", "mystic_role", "valor_role", "instinct_role"][answers.get("team").id],
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
                    except (discord.errors.Forbidden, discord.errors.HTTPException) as e:
                        roles_added = False
                        roles_added_error = e
                    else:
                        await message.edit(
                            content=success(_("Added roles ({roles}) to {user}")).format(
                                roles=cf.humanize_list([str(x) for x in roles["add"]]),
                                user=member.mention,
                            )
                        )
                        roles_added = len(roles["add"])

                roles["remove"] = [ctx.guild.get_role(x) for x in roles["remove"]]
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
                    except (discord.errors.Forbidden, discord.errors.HTTPException) as e:
                        roles_removed = False
                        roles_removed_error = e
                    else:
                        await message.edit(
                            content=success(_("Removed roles ({roles}) from {user}")).format(
                                roles=cf.humanize_list([str(x) for x in roles["remove"]]),
                                user=member.mention,
                            )
                        )
                        roles_removed = len(roles["remove"])

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
                except (discord.errors.Forbidden, discord.errors.HTTPException) as e:
                    nick_set = False
                    nick_set_error = e
                else:
                    await message.edit(
                        content=success(_("Changed {user}‘s nick to {nickname}")).format(
                            user=member.mention, nickname=answers.get("nickname")
                        )
                    )
                    nick_set = True

        async with ctx.typing():
            if assign_roles or set_nickname:
                approval_message = success(_("{user} has been approved!\n")).format(
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
                message: discord.Message = await ctx.send(loading(""))

        log.info(
            "Attempting to add {user} to database, checking if they already exist".format(
                user=answers.get("nickname")
            )
        )

        await message.edit(content=loading(_("Checking for user in database")))

        try:
            trainer: client.Trainer = await converters.TrainerConverter().convert(
                ctx, answers.get("nickname"), cli=self.client
            )
        except commands.BadArgument:
            try:
                trainer: client.Trainer = await converters.TrainerConverter().convert(
                    ctx, member, cli=self.client
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
            await trainer.edit(faction=answers.get("team").id, is_verified=True)

            # Check if it's a good idea to update the stats
            set_xp: bool = (
                (answers.get("total_xp") > max(trainer.updates, key=check_xp).total_xp)
                if trainer.updates
                else True
            )
        else:
            log.info(f"{nickname}: No user found, creating profile")
            await message.edit(content=loading(_("Creating {user}")).format(user=nickname))
            trainer: client.Trainer = await self.client.create_trainer(
                username=nickname, faction=answers.get("team").id, is_verified=True
            )
            user = await trainer.user()
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
        notes = introduction_notes(ctx, member, trainer, additional_message=custom_message)

        dm_message = await member.send(notes[0])
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
        embed: discord.Embed = await ProfileCard(
            ctx=ctx, bot=self.bot, client=self.client, trainer=trainer, emoji=self.emoji
        )
        await dm_message.edit(embed=embed)
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
    async def tdxmod__debug(self, ctx: commands.Context, message: discord.Message) -> None:
        """Returns a reason why OCR would have failed"""
        octx = await self.bot.get_context(message)
        async with ctx.channel.typing():
            if await self.bot.cog_disabled_in_guild(self, octx.guild):
                await ctx.send(
                    _(
                        "Message {message.id} failed because the cog is disabled in the guild"
                    ).format(message)
                )
                return

            if len(octx.message.attachments) == 0:
                await ctx.send(
                    _("Message {message.id} failed because there is no file attached.").format(
                        message=message
                    )
                )
                return

            if len(octx.message.attachments) > 1:
                await ctx.send(
                    _("Message {message.id} failed because there more than file attached.").format(
                        message=message
                    )
                )
                return

            profile_ocr: bool = await self.config.channel(octx.channel).profile_ocr()
            if not profile_ocr:
                await ctx.send(
                    _(
                        "Message {message.id} failed because that channel is not enabled for OCR"
                    ).format(message=message)
                )
                return

            try:
                await converters.TrainerConverter().convert(octx, octx.author, cli=self.client)
            except discord.ext.commands.errors.BadArgument:
                await ctx.send(
                    _(
                        "Message {message.id} failed because I couldn't find a TrainerDex user for {message.author}"
                    ).format(message=message)
                )
                return

            try:
                ocr = PogoOCR.ProfileSelf(
                    POGOOCR_TOKEN_PATH, image_uri=octx.message.attachments[0].proxy_url
                )
                ocr.get_text()
            except Exception as e:
                n = await ctx.send(
                    _("Message {message.id} failed because for an unknown reason").format(
                        message=message
                    )
                )
                await ctx.send(cf.box(e))
                msg = str(ocr.text_found[0].description)
                if len(msg) <= 1994:
                    await ctx.send(cf.box(msg))
                else:
                    await n.edit(
                        file=cf.text_to_file(msg, filename=f"full_debug_{message.id}.txt")
                    )
                return
            else:
                msg = str(ocr.text_found[0].description)
                data_found = {
                    "locale": ocr.locale,
                    "number_locale": ocr.number_locale,
                    "username": ocr.username,
                    "buddy_name": ocr.buddy_name,
                    "travel_km": ocr.travel_km,
                    "capture_total": ocr.capture_total,
                    "pokestops_visited": ocr.pokestops_visited,
                    "total_xp": ocr.total_xp,
                    "start_date": ocr.start_date,
                }
                if len(msg) <= 1994:
                    await ctx.send(cf.box(msg))
                else:
                    await ctx.send(file=cf.text_to_file(msg, filename=f"debug_{message.id}.txt"))

                try:
                    df = json.dumps(data_found, default=repr)
                except (TypeError, OverflowError, TypeError):
                    df = data_found
                if len(cf.box(df, lang=("json" if isinstance(df, str) else "py"))) <= 2000:
                    await ctx.send(cf.box(df, lang=("json" if isinstance(df, str) else "py")))
                else:
                    await ctx.send(file=cf.text_to_file(df, filename=f"debug_{message.id}.json"))
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
        roles = await self.config.guild(ctx.guild).roles_to_assign_on_approval()
        add_roles = [ctx.guild.get_role(x) for x in roles["add"]]
        del_roles = [ctx.guild.get_role(x) for x in roles["remove"]]
        team_roles = [
            None,
            ctx.guild.get_role(await self.config.guild(ctx.guild).mystic_role()),
            ctx.guild.get_role(await self.config.guild(ctx.guild).valor_role()),
            ctx.guild.get_role(await self.config.guild(ctx.guild).instinct_role()),
        ]
        print(team_roles)
        members = [x for x in ctx.guild.members if not x.bot]

        members_to_edit = []
        await ctx.send("Starting ({}/{})".format(len(set(members_to_edit)), len(members)))
        for role in add_roles:
            message = await ctx.send(
                "Checking {} ({}/{})".format(role, len(set(members_to_edit)), len(members))
            )
            members_to_edit += [m for m in members if role not in m.roles]
            await message.edit(
                content="Checked `{}` ({}/{})".format(
                    role, len(set(members_to_edit)), len(members)
                )
            )
        for role in del_roles:
            message = await ctx.send(
                "Checking {} ({}/{})".format(role, len(set(members_to_edit)), len(members))
            )
            members_to_edit += [m for m in members if role in m.roles]
            await message.edit(
                content="Checked `{}` ({}/{})".format(
                    role, len(set(members_to_edit)), len(members)
                )
            )
        members_to_edit = list(set(members_to_edit))

        members_approve = 0
        message = await ctx.send(
            "{} approved, {} checked, {} total".format(members_approve, 0, len(members_to_edit))
        )
        async with ctx.typing():
            for index, member in enumerate(members_to_edit):
                try:
                    trainer: client.Trainer = await converters.TrainerConverter().convert(
                        ctx, member, cli=self.client
                    )
                except commands.BadArgument:
                    await message.edit(
                        content="{} approved, {} checked, {} total".format(
                            members_approve, index + 1, len(members_to_edit)
                        )
                    )
                    continue
                if trainer.is_verified:
                    roles_to_add = list(set(add_roles))
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
                        except (discord.Forbidden, discord.HTTPException):
                            pass

                    if del_roles:
                        try:
                            await member.remove_roles(
                                *del_roles,
                                reason=_("{mod} ran the command `{command}`").format(
                                    mod=ctx.author, command=ctx.invoked_with
                                ),
                            )
                        except (discord.Forbidden, discord.HTTPException):
                            pass

                    if set_nickname:
                        try:
                            await member.edit(
                                nick=trainer.nickname,
                                reason=_("{mod} ran the command `{command}`").format(
                                    mod=ctx.author, command=ctx.invoked_with
                                ),
                            )
                        except (discord.Forbidden, discord.HTTPException):
                            pass
                    members_approve += 1
                await message.edit(
                    content="{} approved, {} checked, {} total".format(
                        members_approve, index + 1, len(members_to_edit)
                    )
                )
