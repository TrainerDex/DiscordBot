import asyncio
import json
import logging
import os
import PogoOCR
from contextlib import suppress
from typing import Any, TypedDict, Union
from discord import Thread

from discord.errors import DiscordException, Forbidden, HTTPException
from discord.ext.commands.errors import BadArgument
from discord.member import Member
from discord.message import Message
from discord.role import Role
from discord.ext import commands

from trainerdex.faction import Faction
from trainerdex.trainer import Trainer
from trainerdex.user import User
from trainerdex.update import Update

from trainerdex_discord_bot import converters
from trainerdex_discord_bot.abc import MixinMeta
from trainerdex_discord_bot.constants import POGOOCR_TOKEN_PATH
from trainerdex_discord_bot.datatypes import (
    ChannelConfig,
    GuildConfig,
    StoredRoles,
    TransformedRoles,
)
from trainerdex_discord_bot.embeds import ProfileCard
from trainerdex_discord_bot.utils import chat_formatting
from trainerdex_discord_bot.utils.general import introduction_notes

logger: logging.Logger = logging.getLogger(__name__)


class ModCmds(MixinMeta):
    @commands.command(name="approve", aliases=["ap", "register", "verify"])
    # @checks.mod_or_permissions(manage_roles=True)
    async def approve_trainer(
        self,
        ctx: commands.Context,
        member: Member,
        nickname: converters.NicknameConverter,
        team: converters.TeamConverter,
        total_xp: converters.TotalXPConverter,
    ) -> None:
        """Create a profile in TrainerDex

        If `guild.assign_roles_on_join` or `guild.set_nickname_on_join` are True, it will do those actions before checking the database.

        If a trainer already exists for this profile, it will update the Total XP is needed.

        """
        assign_roles: bool = await self.config.get_guild(ctx.guild).assign_roles_on_join
        set_nickname: bool = await self.config.get_guild(ctx.guild).set_nickname_on_join

        class AnswersFormats(TypedDict):
            nickname: str
            team: Faction
            total_xp: int

        answers: AnswersFormats = {
            "nickname": nickname,
            "team": team,
            "total_xp": total_xp,
        }

        reply: Message = await ctx.reply(chat_formatting.loading("Let's go…"))

        if assign_roles:
            async with ctx.typing():

                stored_roles: StoredRoles = await self.config.get_guild(
                    ctx.guild
                ).roles_to_assign_on_approval

                # Transform stored roles to a list of roles
                roles: TransformedRoles = {
                    key: [ctx.guild.get_role(role_id) for role_id in stored_roles[key]]
                    for key in stored_roles
                }

                if answers["team"].id > 0:
                    team_role: int = self.config.get_guild(ctx.guild).get(
                        ["", "mystic_role", "valor_role", "instinct_role"][answers["team"].id]
                    )
                    if team_role:
                        roles["add"].append(ctx.guild.get_role(team_role))

                if roles["add"]:
                    await reply.edit(
                        content=chat_formatting.loading("Adding roles ({roles}) to {user}").format(
                            roles=chat_formatting.humanize_list([str(x) for x in roles["add"]]),
                            user=member.mention,
                        )
                    )

                    try:
                        await member.add_roles(
                            *roles["add"],
                            reason="{mod} ran the command `{command}`".format(
                                mod=ctx.author, command=ctx.invoked_with
                            ),
                        )
                    except (Forbidden, HTTPException) as e:
                        roles_added: bool = False
                        roles_added_error: DiscordException = e
                    else:
                        await reply.edit(
                            content=chat_formatting.success(
                                "Added roles ({roles}) to {user}"
                            ).format(
                                roles=chat_formatting.humanize_list(
                                    [str(x) for x in roles["add"]]
                                ),
                                user=member.mention,
                            )
                        )
                        roles_added: int = len(roles["add"])

                if roles["remove"]:
                    await reply.edit(
                        content=chat_formatting.loading(
                            "Removing roles ({roles}) from {user}"
                        ).format(
                            roles=chat_formatting.humanize_list([str(x) for x in roles["remove"]]),
                            user=member.mention,
                        )
                    )

                    try:
                        await member.remove_roles(
                            *roles["remove"],
                            reason="{mod} ran the command `{command}`".format(
                                mod=ctx.author, command=ctx.invoked_with
                            ),
                        )
                    except (Forbidden, HTTPException) as e:
                        roles_removed: bool = False
                        roles_removed_error: DiscordException = e
                    else:
                        await reply.edit(
                            content=chat_formatting.success(
                                "Removed roles ({roles}) from {user}"
                            ).format(
                                roles=chat_formatting.humanize_list(
                                    [str(x) for x in roles["remove"]]
                                ),
                                user=member.mention,
                            )
                        )
                        roles_removed: int = len(roles["remove"])

        if set_nickname:
            async with ctx.typing():
                await reply.edit(
                    content=chat_formatting.loading("Changing {user}‘s nick to {nickname}").format(
                        user=member.mention, nickname=answers.get("nickname")
                    )
                )

                try:
                    await member.edit(
                        nick=answers.get("nickname"),
                        reason="{mod} ran the command `{command}`".format(
                            mod=ctx.author, command=ctx.invoked_with
                        ),
                    )
                except (Forbidden, HTTPException) as e:
                    nick_set: bool = False
                    nick_set_error: DiscordException = e
                else:
                    await reply.edit(
                        content=chat_formatting.success(
                            "Changed {user}‘s nick to {nickname}"
                        ).format(user=member.mention, nickname=answers.get("nickname"))
                    )
                    nick_set: bool = True

        async with ctx.typing():
            if assign_roles or set_nickname:
                approval_message: str = chat_formatting.success(
                    "{user} has been approved!\n"
                ).format(user=member.mention)

                if assign_roles:
                    if roles["add"]:
                        if roles_added:
                            approval_message += chat_formatting.success(
                                "{count} role(s) added.\n"
                            ).format(count=roles_added)
                        else:
                            approval_message += chat_formatting.error(
                                "Some roles could not be added. ({roles})\n"
                            ).format(roles=chat_formatting.humanize_list(roles["add"]))
                            approval_message += f"`{roles_added_error}`\n"

                    if roles["remove"]:
                        if roles_removed:
                            approval_message += chat_formatting.success(
                                "{count} role(s) removed.\n"
                            ).format(count=roles_removed)
                        else:
                            approval_message += chat_formatting.error(
                                "Some roles could not be removed. ({roles})\n"
                            ).format(roles=chat_formatting.humanize_list(roles["remove"]))
                            approval_message += f"`{roles_removed_error}`\n"

                if set_nickname:
                    if nick_set:
                        approval_message += chat_formatting.success("User nickname set.\n")
                    else:
                        approval_message += chat_formatting.error(
                            "User nickname could not be set. (`{nickname}`)\n"
                        ).format(nickname=answers.get("nickname"))
                        approval_message += f"`{nick_set_error}`\n"

                await reply.edit(content=approval_message)
                reply: Message = await reply.reply(chat_formatting.loading(""))

        logger.info(
            "Attempting to add %(user)s to database, checking if they already exist",
            {"user": answers.get("nickname")},
        )

        await reply.edit(content=chat_formatting.loading("Checking for user in database"))

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
            await reply.edit(
                content=chat_formatting.loading(
                    "An existing record was found for {user}. Updating details…".format(
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
            await reply.edit(
                content=chat_formatting.loading("Creating {user}").format(user=nickname)
            )
            trainer: Trainer = await self.client.create_trainer(
                username=nickname, faction=answers.get("team").id, is_verified=True
            )
            user: User = await trainer.user()
            await user.add_discord(member)
            await reply.edit(
                content=chat_formatting.loading("Created {user}").format(user=nickname)
            )
            set_xp: bool = True

        if set_xp:
            await reply.edit(
                content=chat_formatting.loading(
                    "Setting Total XP for {user} to {total_xp}."
                ).format(
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
            await reply.edit(
                content=chat_formatting.loading("Won't set Total XP for {user}.").format(
                    user=trainer.username
                )
            )

        custom_message: str = await self.config.get_guild(ctx.guild).introduction_note
        notes: str = introduction_notes(ctx, member, trainer, additional_message=custom_message)

        with suppress(Forbidden):
            await member.send(notes[0])
            if len(notes) == 2:
                await member.send(notes[1])
        await reply.edit(
            content=(
                chat_formatting.success("Successfully added {user} as {trainer}.")
                + "\n"
                + chat_formatting.loading("Loading profile…")
            ).format(
                user=member.mention,
                trainer=trainer.username,
            )
        )
        embed: ProfileCard = await ProfileCard(ctx, client=self.client, trainer=trainer)
        with suppress(Forbidden):
            await member.send(embed=embed)
        await reply.edit(
            content=chat_formatting.success("Successfully added {user} as {trainer}.").format(
                user=member.mention,
                trainer=trainer.username,
            ),
            embed=embed,
        )

    @commands.group(name="mod", case_insensitive=True)
    async def mod(self, ctx: commands.Context) -> None:
        """⬎ TrainerDex-specific Moderation Commands"""
        pass

    @mod.command(name="debug")
    # @checks.mod()
    async def mod__debug(self, ctx: commands.Context, message: Message) -> None:
        """Returns a reason why OCR would have failed"""
        guild_config: GuildConfig = self.config.get_guild(message.guild)
        channel_config: ChannelConfig = self.config.get_channel(message.channel)

        thread: Thread = await ctx.message.create_thread(
            name=f"Debugging OCR for {message.id}", auto_archive_duration=60
        )

        original_context: commands.Context = await self.bot.get_context(message)
        async with thread.typing():
            if not guild_config.enabled:
                await thread.send(
                    f"Message {message.id} failed because the cog is disabled in the guild"
                )

            if not channel_config.profile_ocr:
                await thread.send(
                    f"Message {message.id} failed because OCR is disabled in the channel"
                )

            if len(original_context.message.attachments) == 0:
                await thread.send(
                    f"Message {message.id} failed because there is no file attached."
                )

            if len(original_context.message.attachments) > 1:
                await thread.send(
                    f"Message {message.id} failed because there more than file attached."
                )

            if os.path.splitext(original_context.message.attachments[0].proxy_url)[
                1
            ].lower() not in [
                ".jpeg",
                ".jpg",
                ".png",
            ]:
                await thread.send(
                    f"Message {message.id} failed because the file is not jpg or png."
                )
                return

            try:
                await converters.TrainerConverter().convert(
                    original_context, original_context.author, cli=self.client
                )
            except BadArgument:
                await thread.send(
                    f"Message {message.id} failed because I couldn't find a TrainerDex user for {message.author}"
                )
                return

            try:
                ocr: PogoOCR.ProfileSelf = PogoOCR.ProfileSelf(
                    POGOOCR_TOKEN_PATH, image_uri=original_context.message.attachments[0].proxy_url
                )
                ocr.get_text()
            except Exception as e:
                reply: Message = await thread.send(
                    f"Message {message.id} failed because for an unknown reason"
                )
                reply = await reply.reply(chat_formatting.box(e))

                message_content: str = str(ocr.text_found[0].description)
                for page in chat_formatting.pagify(message_content, page_length=1994):
                    reply = await reply.reply(chat_formatting.box(page))
                    await asyncio.sleep(0.5)
                return
            else:
                message_content: str = str(ocr.text_found[0].description)
                reply: Message = await thread.send(f"Message {message.id} should have succeeded")
                for page in chat_formatting.pagify(message_content, page_length=1994):
                    reply = await reply.reply(chat_formatting.box(page))
                    await asyncio.sleep(0.5)

                data_found: dict[str, Any] = {
                    "username": ocr.username,
                    "buddy_name": ocr.buddy_name,
                    "travel_km": str(ocr.travel_km),
                    "capture_total": ocr.capture_total,
                    "pokestops_visited": ocr.pokestops_visited,
                    "total_xp": ocr.total_xp,
                    "start_date": ocr.start_date and ocr.start_date.isoformat(),
                }

                message_content: str = str(ocr.text_found[0].description)
                for page in chat_formatting.pagify(json.dumps(data_found), page_length=1994):
                    reply = await reply.reply(chat_formatting.box(page, lang="json"))
                    await asyncio.sleep(0.5)
                return

    @mod.command(name="auto-role")
    # @checks.mod_or_permissions(manage_roles=True)
    async def autorole(self, ctx: commands.Context) -> None:
        """EXPERIMENTAL: Checks for existing users that don't have the right roles, and applies them

        Warning: This command is slow and experimental. I wouldn't recommend running it without checking by your roles_to_assign_on_approval setting first.
        It can really mess with roles on a mass scale.
        """
        guild_config: GuildConfig = self.config.get_guild(ctx.guild)
        if not guild_config.assign_roles_on_join:
            return
        add_roles: list[Role] = [
            ctx.guild.get_role(x) for x in guild_config.roles_to_assign_on_approval.add
        ]
        del_roles: list[Role] = [
            ctx.guild.get_role(x) for x in guild_config.roles_to_assign_on_approval.remove
        ]
        team_roles: list[Union[None, Role]] = [
            None,
            ctx.guild.get_role(guild_config.mystic_role),
            ctx.guild.get_role(guild_config.valor_role),
            ctx.guild.get_role(guild_config.instinct_role),
        ]
        members: list[Member] = [x for x in ctx.guild.members if not x.bot]

        members_to_edit: list[Member] = []
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
                    roles_to_add: list[Role] = list(set(add_roles))
                    if trainer.faction > 0:
                        roles_to_add.append(team_roles[trainer.faction])
                    if roles_to_add:
                        try:
                            await member.add_roles(
                                *roles_to_add,
                                reason="{mod} ran the command `{command}`".format(
                                    mod=ctx.author, command=ctx.invoked_with
                                ),
                            )
                        except (Forbidden, HTTPException):
                            pass

                    if del_roles:
                        try:
                            await member.remove_roles(
                                *del_roles,
                                reason="{mod} ran the command `{command}`".format(
                                    mod=ctx.author, command=ctx.invoked_with
                                ),
                            )
                        except (Forbidden, HTTPException):
                            pass

                    if guild_config.set_nickname_on_join:
                        try:
                            await member.edit(
                                nick=trainer.nickname,
                                reason="{mod} ran the command `{command}`".format(
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
