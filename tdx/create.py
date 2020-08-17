import logging
from typing import Any, Callable, Optional, Union

import discord
from redbot.core import checks, commands
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf, predicates

from . import converters, client
from .abc import MixinMeta
from .profile import Profile
from .embeds import ProfileCard
from .utils import check_xp, introduction_notes, loading, success

log: logging.Logger = logging.getLogger(__name__)
_ = Translator("TrainerDex", __file__)

AbandonQuestionException = Exception
NoAnswerProvidedException = Exception


class Question:
    def __init__(
        self,
        ctx,
        question: str,
        message: Optional[discord.Message] = None,
        predicate: Optional[Callable] = None,
    ) -> None:
        self._ctx = ctx
        self.question = question
        self.message = message
        if predicate:
            self.predicate = predicate
        else:
            self.predicate = predicates.MessagePredicate.same_context(self._ctx)
        self.response = None

    async def ask(self) -> Union[str, None]:
        if self.message:
            await self.message.edit(
                content=cf.question(f"{self._ctx.author.mention}: {self.question}")
            )
        else:
            self.message = await self._ctx.send(
                content=cf.question(f"{self._ctx.author.mention}: {self.question}")
            )
        self.response = await self._ctx.bot.wait_for("message", check=self.predicate)
        if self.responce.content.lower() == f"{self._ctx.prefix}cancel":
            # TODO: Make an actual exception class
            raise AbandonQuestionException
        else:
            return self.answer

    async def append_answer(self, answer: Optional[str] = None) -> None:
        content = "{q}\n{a}".format(
            q=self.question, a=(answer if answer is not None else self.answer)
        )
        await self.message.edit(content=content)

    @property
    def answer(self) -> Union[str, None]:
        if self.response:
            return self.response.content
        return None


class ProfileCreate(MixinMeta):
    profile = Profile.profile

    async def ask_question(
        self,
        ctx,
        question: str,
        optional: bool = False,
        predicate: Optional[Callable] = None,
        converter: Optional[Callable[[discord.Context, str], Any]] = None,
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
            await q.response.delete()

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

    @profile.command(name="create", aliases=["register", "approve", "verify"])
    @checks.mod_or_permissions(manage_roles=True)
    async def profile__create(
        self,
        ctx: commands.Context,
        member: discord.Member,
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

        if nickname is None:
            try:
                nickname = await self.ask_question(
                    ctx,
                    question=_("What is the in-game username of {mention}?").format(
                        mention=mention
                    ),
                    converter=converters.NicknameConverter,
                )
            except NoAnswerProvidedException:
                await ctx.send(_("Answer could not be determined. Abandoning!"))
                return

        if team is None:
            try:
                team = await self.ask_question(
                    ctx,
                    question=_("What team is {nickname} in?").format(nickname=nickname),
                    converter=converters.TeamConverter,
                )
            except NoAnswerProvidedException:
                await ctx.send(_("Answer could not be determined. Abandoning!"))
                return

        MINIMUM_XP_CAP = 100
        if (total_xp is None) or (total_xp <= MINIMUM_XP_CAP):
            try:
                total_xp = await self.ask_question(
                    ctx,
                    question=_("What is {nickname}‘s Total XP? (as a whole number)").format(
                        nickname=nickname
                    ),
                    predicate=predicates.MessagePredicate.valid_int(ctx),
                )
            except NoAnswerProvidedException:
                await ctx.send(_("Answer could not be determined. Abandoning!"))
                return
            total_xp = int(total_xp)

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
                        user=member.mention, nickname=nickname
                    )
                )

                try:
                    await member.edit(
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
                            user=member.mention, nickname=nickname
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
            await user.add_discord(member)
            await message.edit(content=loading(_("Created {user}")).format(user=nickname))
            set_xp: bool = True

        if set_xp:
            await message.edit(
                content=loading(_("Setting Total XP for {user} to {total_xp}.")).format(
                    user=trainer.username, total_xp=total_xp,
                )
            )
            await trainer.post(
                stats={"total_xp": total_xp},
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
                user=member.mention, trainer=trainer.username,
            )
        )
        embed: discord.Embed = await ProfileCard(
            ctx=ctx, bot=self.bot, client=self.client, trainer=trainer, emoji=self.emoji
        )
        await dm_message.edit(embed=embed)
        await message.edit(
            content=success(_("Successfully added {user} as {trainer}.")).format(
                user=member.mention, trainer=trainer.username,
            ),
            embed=embed,
        )
