from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo
from typing import Mapping, Optional

import discord.errors
from aiohttp import ClientResponseError
from discord import (
    ApplicationContext,
    Member,
    Option,
    OptionChoice,
    Permissions,
    Role,
    WebhookMessage,
    slash_command,
)
from discord.utils import snowflake_time

from trainerdex.api.trainer import Trainer
from trainerdex.api.update import Update
from trainerdex.discord_bot.checks import check_member_privilage
from trainerdex.discord_bot.constants import Stats
from trainerdex.discord_bot.datatypes import GuildConfig
from trainerdex.discord_bot.embeds import ProfileCard
from trainerdex.discord_bot.modules.base import Module
from trainerdex.discord_bot.utils.chat_formatting import format_numbers
from trainerdex.discord_bot.utils.converters import get_trainer
from trainerdex.discord_bot.utils.deadlines import SHUTDOWN_DATE


class ModerationModule(Module):
    @classmethod
    @property
    def METADATA_ID(cls) -> str:
        return "ModCog"

    async def allowed_to_rename(self, ctx: ApplicationContext) -> bool:
        if not (await self.config.get_guild(ctx.guild.id)).set_nickname_on_join:
            return False

        if await check_member_privilage(ctx):
            return True

        return bool(ctx.author.guild_permissions.manage_nicknames)

    async def allowed_to_assign_roles(self, ctx: ApplicationContext) -> bool:
        if not (await self.config.get_guild(ctx.guild.id)).assign_roles_on_join:
            return False

        if await check_member_privilage(ctx):
            return True

        return bool(ctx.author.guild_permissions.manage_roles)

    def allowed_to_create_profiles(self) -> bool:
        return datetime.now(ZoneInfo("UTC")) < SHUTDOWN_DATE

    def compare_stats(self, x: Update, y: Mapping[str, int | Decimal | None], /) -> bool:
        x_, y_ = vars(x), deepcopy(y)
        # Clean out unwanted values from both dicts
        for update in x_, y_:
            update = {
                key: value
                for key, value in update.items()
                if (key in ("total_xp", "travel_km", "capture_total", "pokestops_visited")) and (value is not None)
            }

        # We want to ensure that the values in y are always larger than their counterpart in x
        for key, y_value in y_.items():
            if (x_value := x_.get(key)) and y_value < x_value:
                return False
        return True

    def get_stat_name(self, stat: str) -> str:
        if stat_enum := Stats.__dict__.get(stat.upper()):
            return stat_enum.value[1]
        return stat

    @slash_command(
        name="approve",
        checks=[check_member_privilage],
        default_member_permissions=Permissions(0x20),
        guild_only=True,
        options=[
            Option(
                Member,
                name="member",
                description="Target member to approve, cannot be a bot.",
                required=True,
            ),
            Option(
                str,
                name="nickname",
                description="The user's Pokémon Go nickname.",
                required=True,
            ),
            Option(
                int,
                name="team",
                description="The user's Pokémon Go team",
                choices=[
                    OptionChoice("No Team (Grey)", 0),
                    OptionChoice("Mystic", 1),
                    OptionChoice("Valor", 2),
                    OptionChoice("Instinct", 3),
                ],
                required=True,
            ),
            Option(
                int,
                name="total_xp",
                description="Total XP",
                required=True,
            ),
            Option(
                float,
                name="travel_km",
                description="Distance Walked",
                required=False,
            ),
            Option(
                int,
                name="capture_total",
                description="Pokémon Caught",
                required=False,
            ),
            Option(
                int,
                name="pokestops_visited",
                description="PokéStops Visited",
                required=False,
            ),
        ],
    )
    async def slash__approve(
        self,
        ctx: ApplicationContext,
        member: Member,
        nickname: str,
        team: int,
        total_xp: int,
        travel_km: Optional[float] = None,
        capture_total: Optional[int] = None,
        pokestops_visited: Optional[int] = None,
    ) -> None:
        """Create a profile in TrainerDex

        If `guild.assign_roles_on_join` or `guild.set_nickname_on_join` are True,
        it will do those actions before checking the database.

        If a trainer already exists for this profile, it will update the stats as needed.
        """
        if not isinstance(member, Member):
            await ctx.respond("This user is no longer in this server. Unable to approve.")
            return

        if member.bot:
            await ctx.respond("You can't approve bots.")
            return

        await ctx.interaction.response.defer()
        ctx.interaction.response._responded = True
        reason = f"{ctx.author} used the /approve command to grant {member} access to this guild."

        allowed_to_rename: bool = await self.allowed_to_rename(ctx)
        allowed_to_assign_roles: bool = await self.allowed_to_assign_roles(ctx)
        allowed_to_create_profile: bool = self.allowed_to_create_profiles()

        roles_remove, roles_add = set(), set()
        actions_commited = []

        if allowed_to_assign_roles:
            guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
            roles_remove: set[int] = set(guild_config.roles_to_assign_on_approval.remove)
            roles_add: set[int] = set(guild_config.roles_to_assign_on_approval.add)

            match team:
                case 1:
                    if guild_config.mystic_role:
                        roles_add.add(guild_config.mystic_role)
                case 2:
                    if guild_config.valor_role:
                        roles_add.add(guild_config.valor_role)
                case 3:
                    if guild_config.instinct_role:
                        roles_add.add(guild_config.instinct_role)

            if roles_remove:
                roles_remove: list[Role | None] = [ctx.guild.get_role(id) for id in roles_remove]
                roles_remove: list[Role] = [role for role in roles_remove if role is not None]
                try:
                    await member.remove_roles(*roles_remove, reason=reason)
                except discord.errors.Forbidden:
                    actions_commited.append(
                        (
                            "Attempted to remove these roles, but errors were raised "
                            "(possibly insufficient permissions): {}"
                        ).format(", ".join([role.name for role in roles_remove]))
                    )
                else:
                    actions_commited.append(
                        "Removed roles: {}".format(", ".join([role.name for role in roles_remove]))
                    )

            if roles_add:
                roles_add: list[Role | None] = [ctx.guild.get_role(id) for id in roles_add]
                roles_add: list[Role] = [role for role in roles_add if role is not None]
                try:
                    await member.add_roles(*roles_add, reason=reason)
                except discord.errors.Forbidden:
                    actions_commited.append(
                        (
                            "Attempted to add these roles, but errors were raised "
                            "(possibly insufficient permissions): {}"
                        ).format(", ".join([role.name for role in roles_add]))
                    )
                else:
                    actions_commited.append("Added roles: {}".format(", ".join([role.name for role in roles_add])))

        if allowed_to_rename:
            try:
                await member.edit(nick=nickname, reason=reason)
            except discord.errors.Forbidden:
                pass
            else:
                actions_commited.append(f"Discord Member nickname changed to {nickname}")

        async with self.client() as client:
            trainer: Trainer | None = await get_trainer(
                client,
                nickname=nickname,
                user=member,
                prefetch_updates=True,
            )

            if trainer is None:
                if not allowed_to_create_profile:
                    actions_commited.append(
                        (
                            "Trainer registation is disabled."
                            f" TrainerDex is being retired on <t:{int(SHUTDOWN_DATE.timestamp())}:D>"
                        )
                    )
                else:
                    try:
                        trainer: Trainer = await client.create_trainer(
                            username=nickname, faction=team, verified=True
                        )
                        await (await trainer.get_user()).add_discord(member)
                    except ClientResponseError as e:
                        actions_commited.append(f"Failed to create trainer: {e}")
                    else:
                        actions_commited.append(f"Registered new trainer with nickname: {nickname}")

            # Only continue if trainer object exists
            if trainer:
                new_stats = {
                    key: value
                    for key, value in {
                        "total_xp": total_xp,
                        "travel_km": travel_km,
                        "capture_total": capture_total,
                        "pokestops_visited": pokestops_visited,
                    }.items()
                    if value is not None
                }

                try:
                    latest_update_with_total_xp: Update = max(trainer.updates, key=lambda x: (x.total_xp or 0))
                except ValueError:
                    post_update: bool = True
                else:
                    post_update: bool = self.compare_stats(latest_update_with_total_xp, new_stats)

                if post_update:
                    await trainer.post(
                        data_source="ts_social_discord",
                        stats=new_stats,
                        update_time=snowflake_time(ctx.interaction.id),
                    )
                    stats_humanize = ", ".join(
                        [
                            f"{self.get_stat_name(key)}: {format_numbers(value)}"
                            for key, value in new_stats.items()
                            if value is not None
                        ]
                    )
                    actions_commited.append(f"Updated {trainer.username} with new stats; {stats_humanize}")

            if actions_commited:
                response: WebhookMessage = await ctx.respond(
                    f"`/approve` run on {member.mention}\n" + "\n".join(actions_commited),
                    wait=True,
                )

                if trainer:
                    embed: ProfileCard = await ProfileCard(self._common, ctx, trainer=trainer)
                    await response.edit(embed=embed)
                    await embed.show_progress()
                    await response.edit(embed=embed)
                    await embed.add_leaderboard()
                    await response.edit(embed=embed)
                    await embed.add_guild_leaderboard(ctx.guild)
                    await response.edit(embed=embed)
