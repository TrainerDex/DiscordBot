from __future__ import annotations

from asyncio import gather
from datetime import datetime, time
from enum import Enum
from typing import TYPE_CHECKING, Literal
from zoneinfo import ZoneInfo

from discord import Guild
from discord.commands import ApplicationContext, Option, OptionChoice, slash_command
from discord.ext import tasks

from trainerdex_discord_bot.cogs.interface import Cog
from trainerdex_discord_bot.constants import Stats
from trainerdex_discord_bot.utils.general import send
from trainerdex_discord_bot.views.leaderboard import LeaderboardView

if TYPE_CHECKING:
    from trainerdex.leaderboard import BaseLeaderboard

    from trainerdex_discord_bot.datatypes import GuildConfig


class LeaderboardType(Enum):
    GUILD = "guild", "Discord Server"
    GLOBAL = "global", "Global"


class LeaderboardCog(Cog):
    async def __post_init__(self) -> None:
        self._gather_guilds_for_weekly_leaderboards.start()
        return await super().__post_init__()

    def cog_unload(self) -> None:
        self._gather_guilds_for_weekly_leaderboards.cancel()
        return super().cog_unload()

    @slash_command(
        name="leaderboard",
        description="Returns a leaderboard",
        options=[
            Option(
                str,
                name="selection",
                choices=[OptionChoice(item.value[1], item.value[0]) for item in LeaderboardType],
                default=LeaderboardType.GUILD.value[0],
            ),
            Option(
                str,
                name="stat",
                choices=[OptionChoice(item.value[1], item.value[0]) for item in Stats][:25],
                default=Stats.TOTAL_XP.value[0],
            ),
        ],
    )
    async def leaderboard(
        self,
        ctx: ApplicationContext,
        selection: str,
        stat: str,
    ) -> None:
        await ctx.defer()

        if not ctx.guild:
            selection = LeaderboardType.GLOBAL.value[0]

        leaderboard_data: BaseLeaderboard = await self.client.get_leaderboard(
            stat=stat,
            guild=ctx.guild if selection == LeaderboardType.GUILD.value[0] else None,
        )

        if len(leaderboard_data) < 1:
            await send(ctx, content="No results to display!")
        else:
            paginator = await LeaderboardView.create(ctx, leaderboard_data)
            await paginator.respond(ctx.interaction)

    @tasks.loop(time=[time(x) for x in range(24)])
    # @tasks.loop(minutes=1)
    async def _gather_guilds_for_weekly_leaderboards(self):
        enabled_guilds = {}

        for guild in self.bot.guilds:
            guild_config = await self.config.get_guild(guild)
            if guild_config.is_eligible_for_leaderboard:
                enabled_guilds[guild] = guild_config

        gather(
            *(
                self._post_weekly_leaderboard(guild, guild_config)
                for guild, guild_config in enabled_guilds.items()
            )
        )

    @_gather_guilds_for_weekly_leaderboards.before_loop
    async def loop_wait(self):
        await self.bot.wait_until_ready()

    async def _post_weekly_leaderboard(self, guild: Guild, config: GuildConfig):
        guild_timezone = ZoneInfo(config.timezone or "UTC")
        leaderboard_channel = self.bot.get_channel(config.leaderboard_channel_id)

        if (time_now := datetime.now(tz=guild_timezone)).hour == 12:
            await leaderboard_channel.send(
                f"It's {time_now.strftime('%H:%M %Z')}, time to post the weekly leaderboard! Unfortunately, they're still a work in progress.\nThis message will self-destruct in 30 seconds.",
                delete_after=30,
            )
