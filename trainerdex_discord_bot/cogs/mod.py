from __future__ import annotations

import logging
from contextlib import suppress
from typing import TYPE_CHECKING

from discord import (
    ApplicationContext,
    Member,
    Option,
    OptionChoice,
    Permissions,
    WebhookMessage,
    slash_command,
)
from discord.errors import Forbidden, HTTPException

from trainerdex_discord_bot import checks
from trainerdex_discord_bot.cogs.interface import Cog
from trainerdex_discord_bot.datatypes import GuildConfig
from trainerdex_discord_bot.embeds import ProfileCard
from trainerdex_discord_bot.utils import chat_formatting
from trainerdex_discord_bot.utils.converters import get_trainer
from trainerdex_discord_bot.utils.general import introduction_notes

if TYPE_CHECKING:
    from trainerdex.trainer import Trainer
    from trainerdex.update import Update
    from trainerdex.user import User

    from trainerdex_discord_bot.datatypes import StoredRoles, TransformedRoles

logger: logging.Logger = logging.getLogger(__name__)


class ModCog(Cog):
    @slash_command(
        name="approve",
        checks=[checks.has_permissions(Permissions(0x10000000))],
        options=[
            Option(Member, name="member"),
            Option(str, name="nickname", description="The user's Pokemon Go username"),
            Option(
                int,
                name="team",
                description="The user's Pokemon Go team",
                choices=[
                    OptionChoice("No Team", 0),
                    OptionChoice("Mystic", 1),
                    OptionChoice("Valor", 2),
                    OptionChoice("Instinct", 3),
                ],
            ),
            Option(int, name="total_xp"),
        ],
    )
    async def approve_trainer(
        self,
        ctx: ApplicationContext,
        member: Member,
        nickname: str,
        team: int,
        total_xp: int,
    ) -> None:
        """Create a profile in TrainerDex

        If `guild.assign_roles_on_join` or `guild.set_nickname_on_join` are True, it will do those actions before checking the database.

        If a trainer already exists for this profile, it will update the Total XP is needed.

        """
        guild_config: GuildConfig = self.config.get_guild(ctx.guild)

        await ctx.defer()

        # if guild_config.assign_roles_on_join:
        #     async with ctx.typing():

        #         stored_roles: StoredRoles = await self.config.get_guild(
        #             ctx.guild
        #         ).roles_to_assign_on_approval

        #         # Transform stored roles to a list of roles
        #         roles: TransformedRoles = {
        #             key: [ctx.guild.get_role(role_id) for role_id in stored_roles[key]]
        #             for key in stored_roles
        #         }

        #         if team > 0:
        #             team_role: int = await self.config.get_guild(ctx.guild).get(
        #                 ["", "mystic_role", "valor_role", "instinct_role"][team]
        #             )
        #             if team_role:
        #                 roles["add"].append(ctx.guild.get_role(team_role))

        #         if roles["add"]:
        #             await ctx.respond(
        #                 chat_formatting.loading("Adding roles ({roles}) to {user}").format(
        #                     roles=chat_formatting.humanize_list([str(x) for x in roles["add"]]),
        #                     user=member.mention,
        #                 )
        #             )

        #             try:
        #                 await member.add_roles(
        #                     *roles["add"],
        #                     reason="{mod} ran the command `{command}`".format(
        #                         mod=ctx.author, command=ctx.invoked_with
        #                     ),
        #                 )
        #             except (Forbidden, HTTPException) as e:
        #                 roles_added: bool = False
        #                 roles_added_error: DiscordException = e
        #             else:
        #                 await ctx.respond(
        #                     chat_formatting.success("Added roles ({roles}) to {user}").format(
        #                         roles=chat_formatting.humanize_list(
        #                             [str(x) for x in roles["add"]]
        #                         ),
        #                         user=member.mention,
        #                     )
        #                 )
        #                 roles_added: int = len(roles["add"])

        #         if roles["remove"]:
        #             await ctx.respond(
        #                 chat_formatting.loading("Removing roles ({roles}) from {user}").format(
        #                     roles=chat_formatting.humanize_list([str(x) for x in roles["remove"]]),
        #                     user=member.mention,
        #                 )
        #             )

        #             try:
        #                 await member.remove_roles(
        #                     *roles["remove"],
        #                     reason="{mod} ran the command `{command}`".format(
        #                         mod=ctx.author, command=ctx.invoked_with
        #                     ),
        #                 )
        #             except (Forbidden, HTTPException) as e:
        #                 roles_removed: bool = False
        #                 roles_removed_error: DiscordException = e
        #             else:
        #                 await ctx.respond(
        #                     chat_formatting.success("Removed roles ({roles}) from {user}").format(
        #                         roles=chat_formatting.humanize_list(
        #                             [str(x) for x in roles["remove"]]
        #                         ),
        #                         user=member.mention,
        #                     )
        #                 )
        #                 roles_removed: int = len(roles["remove"])

        if guild_config.set_nickname_on_join:
            try:
                await member.edit(
                    nick=nickname,
                    reason="{mod} ran the command `{command}`".format(
                        mod=ctx.author, command=ctx.command
                    ),
                )
            except (Forbidden, HTTPException) as e:
                self.bot.on_application_command_error(ctx, e)
            else:
                await ctx.respond(
                    chat_formatting.success(f"Changed {member.mention}‘s nick to {nickname}")
                )

        logger.info(
            "Attempting to add %(user)s to database, checking if they already exist",
            {"user": nickname},
        )

        trainer: Trainer = await get_trainer(self.client, nickname=nickname, user=member)

        if trainer is not None:
            logger.info("We found a trainer: %(trainer)s", {"trainer": trainer.username})
            await ctx.respond(
                chat_formatting.loading(
                    f"An existing record was found for {trainer.username}. Updating details…"
                )
            )

            # Edit the trainer instance with the new team and set is_verified
            # Chances are, is_verified might have been False and this will fix that.
            await trainer.edit(faction=team, is_verified=True)

            # Check if it's a good idea to update the stats
            await trainer.fetch_updates()
            latest_update_with_total_xp: Update = trainer.get_latest_update_for_stat("total_xp")
            set_xp: bool = (
                (total_xp > latest_update_with_total_xp.total_xp) if trainer.updates else True
            )
        else:
            logger.info("%s: No user found, creating profile", nickname)
            trainer: Trainer = await self.client.create_trainer(
                username=nickname, faction=team, is_verified=True
            )
            user: User = await trainer.user()
            await user.add_discord(member)
            await ctx.respond(chat_formatting.loading("Created {user}").format(user=nickname))
            set_xp: bool = True

        if set_xp:
            await trainer.post(
                stats={"total_xp": total_xp},
                data_source="ss_ocr",
                update_time=ctx.message.created_at,
            )

        notes: str = introduction_notes(
            ctx,
            member,
            trainer,
            additional_message=guild_config.introduction_note,
        )
        with suppress(Forbidden):
            for page in chat_formatting.pagify(notes):
                await member.send(page)

        final: WebhookMessage = await ctx.respond(
            chat_formatting.success(f"Successfully added {member.mention} as {trainer.username}.")
        )

        embed: ProfileCard = await ProfileCard(self._common, ctx, trainer=trainer)

        final.edit(embed=embed)
