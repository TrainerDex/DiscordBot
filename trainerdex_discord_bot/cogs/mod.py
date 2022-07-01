from copy import deepcopy
from decimal import Decimal
from typing import Mapping, Optional

from aiohttp import ClientResponseError
import discord.errors
from discord import (
    ApplicationContext,
    Member,
    Option,
    OptionChoice,
    WebhookMessage,
    slash_command,
)
from discord.object import Object
from discord.utils import snowflake_time
from trainerdex.trainer import Trainer
from trainerdex.update import Update

from trainerdex_discord_bot.cogs.interface import Cog
from trainerdex_discord_bot.constants import Stats
from trainerdex_discord_bot.datatypes import GuildConfig
from trainerdex_discord_bot.embeds import ProfileCard
from trainerdex_discord_bot.utils.chat_formatting import format_numbers
from trainerdex_discord_bot.utils.converters import get_trainer


class ModCog(Cog):
    async def cog_check(self, ctx: ApplicationContext) -> bool:
        """A special method that registers as a :func:`~discord.ext.commands.check`
        for every command and subcommand in this cog.

        This function **can** be a coroutine and must take a sole parameter,
        ``ctx``, to represent the :class:`.Context`.
        """
        return await self.check_member_privilage(ctx)

    async def check_member_privilage(
        self,
        ctx: ApplicationContext,
        /,
        *,
        member: Optional[Member] = None,
    ) -> bool:
        """A coroutine that returns whether the user is considered a privilaged or not.

        Checks if the user is a mod by checking if the user has one of the mod roles as defined in the settings.
        Also checks if the user is the owner of the bot, an admin of the guild or has manage_guild permission.
        If any of these checks pass, the user is considered privilaged.

        """
        if member is None:
            member = ctx.author

        if await ctx.bot.is_owner(member):
            return True

        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            return True

        for role_id in (await self.config.get_guild(member.guild.id)).mod_role_ids:
            if member.get_role(role_id):
                return True

        return False

    async def allowed_to_rename(self, ctx: ApplicationContext) -> bool:
        if not (await self.config.get_guild(ctx.guild.id)).set_nickname_on_join:
            return False

        if await self.check_member_privilage(ctx):
            return True

        if ctx.author.guild_permissions.manage_nicknames:
            return True

        return False

    async def allowed_to_assign_roles(self, ctx: ApplicationContext) -> bool:
        if not (await self.config.get_guild(ctx.guild.id)).assign_roles_on_join:
            return False

        if await self.check_member_privilage(ctx):
            return True

        if ctx.author.guild_permissions.manage_roles:
            return True

        return False

    def compare_stats(self, x: Update, y: Mapping[str, int | Decimal | None], /) -> bool:
        x_, y_ = vars(x), deepcopy(y)
        # Clean out unwanted values from both dicts
        for update in x_, y_:
            update = {
                key: value
                for key, value in update.items()
                if (key in ("total_xp", "travel_km", "capture_total", "pokestops_visited"))
                and (value is not None)
            }

        # We want to ensure that the values in y are always larger than their counterpart in x
        for key, value in y_.items():
            if key in x_ and value < x_[key]:
                return False
        return True

    def get_stat_name(self, stat: str) -> str:
        if stat_enum := Stats.__dict__.get(stat.upper()):
            return stat_enum.value[1]
        return stat

    @slash_command(
        name="approve",
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
                description="Your Pokemon Go nickname.",
                required=True,
            ),
            Option(
                int,
                name="team",
                description="The user's Pokemon Go team",
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
                description="Pokemon Caught",
                required=False,
            ),
            Option(
                int,
                name="pokestops_visited",
                description="Pokestops Visited",
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

        If `guild.assign_roles_on_join` or `guild.set_nickname_on_join` are True, it will do those actions before checking the database.

        If a trainer already exists for this profile, it will update the stats as needed.
        """
        if member.bot:
            await ctx.send("You can't approve bots.")
            return

        await ctx.interaction.response.defer()
        reason = f"{ctx.author} used the /approve command to grant {member} access to this guild."

        allowed_to_rename: bool = await self.allowed_to_rename(ctx)
        allowed_to_assign_roles: bool = await self.allowed_to_assign_roles(ctx)

        roles_remove, roles_add = set(), set()
        actions_commited = []

        if allowed_to_assign_roles:
            guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
            roles_remove = set(guild_config.roles_to_assign_on_approval.remove)
            roles_add = set(guild_config.roles_to_assign_on_approval.add)

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
                try:
                    await member.remove_roles(*[Object(x) for x in roles_remove], reason=reason)
                except discord.errors.Forbidden:
                    actions_commited.append(
                        "Attempted to remove these roles, but errors were raised (possibly insufficient permissions): {}".format(
                            ", ".join(
                                [
                                    ctx.guild.get_role(role_id).name or role_id
                                    for role_id in roles_remove
                                ]
                            )
                        )
                    )
                else:
                    actions_commited.append(
                        "Removed roles: {}".format(
                            ", ".join(
                                [
                                    ctx.guild.get_role(role_id).name or role_id
                                    for role_id in roles_remove
                                ]
                            )
                        )
                    )

            if roles_add:
                try:
                    await member.add_roles(*[Object(x) for x in roles_add], reason=reason)
                except discord.errors.Forbidden:
                    actions_commited.append(
                        "Attempted to add these roles, but errors were raised (possibly insufficient permissions): {}".format(
                            ", ".join(
                                [
                                    ctx.guild.get_role(role_id).name or role_id
                                    for role_id in roles_remove
                                ]
                            )
                        )
                    )
                else:
                    actions_commited.append(
                        "Added roles: {}".format(
                            ", ".join(
                                [
                                    ctx.guild.get_role(role_id).name or role_id
                                    for role_id in roles_add
                                ]
                            )
                        )
                    )

        if allowed_to_rename:
            try:
                await member.edit(nick=nickname, reason=reason)
            except discord.errors.Forbidden:
                pass
            else:
                actions_commited.append(f"Discord Member nickname changed to {nickname}")

        trainer: Trainer | None = await get_trainer(
            self.client, nickname=nickname, user=member, prefetch_updates=True
        )

        if trainer is None:
            try:
                trainer: Trainer = await self.client.create_trainer(
                    username=nickname, faction=team, is_verified=True
                )
                await (await trainer.user()).add_discord(member)
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
                latest_update_with_total_xp: Update = trainer.get_latest_update_for_stat(
                    "total_xp"
                )
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
                actions_commited.append(
                    f"Updated {trainer.nickname} with new stats; {stats_humanize}"
                )

        if actions_commited:
            response: WebhookMessage = await ctx.followup.send(
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
