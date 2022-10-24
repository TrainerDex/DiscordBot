from __future__ import annotations

from asyncio import gather
from datetime import date, datetime, time
from enum import Enum
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import aiohttp
from dateutil.relativedelta import MO, relativedelta
from discord import Guild, Message, Thread
from discord.commands import ApplicationContext, Option, OptionChoice, slash_command
from discord.ext import tasks
from yarl import URL

from trainerdex.discord_bot.cogs.interface import Cog
from trainerdex.discord_bot.constants import TRAINERDEX_API_TOKEN, Stats
from trainerdex.discord_bot.utils.chat_formatting import format_time
from trainerdex.discord_bot.utils.general import send
from trainerdex.discord_bot.views.gains_leaderboard import GainsLeaderboardView
from trainerdex.discord_bot.views.leaderboard import LeaderboardView

if TYPE_CHECKING:
    from trainerdex.api.leaderboard import BaseLeaderboard

    from trainerdex.discord_bot.datatypes import GuildConfig


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

        async with self.client() as client:
            leaderboard_data: BaseLeaderboard = await client.get_leaderboard(
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

        local_time = datetime.now(tz=guild_timezone)

        if local_time.hour == 12 and (
            local_time.weekday() == 0 or local_time.date() == date(2022, 8, 10)
        ):
            minuend_datetime = local_time + relativedelta(
                hour=12, minute=0, second=0, microsecond=0
            )
            subtrahend_datetime = minuend_datetime - relativedelta(weeks=1)
            deadline = minuend_datetime + relativedelta(days=1, weekday=MO)

            leaderboard_data: dict[Stats, dict] = {
                stat: (
                    await self._get_gains_leaderboard_data(
                        guild.id, stat.value[0], subtrahend_datetime, minuend_datetime
                    )
                )
                for stat in (
                    Stats.TOTAL_XP,
                    Stats.TRAVEL_KM,
                    Stats.CAPTURE_TOTAL,
                    Stats.POKESTOPS_VISITED,
                    Stats.GYM_GOLD,
                )
            }
            combo_post = GainsLeaderboardView.format_combo_embed(
                leaderboard_data, minuend_datetime
            )

            message: Message = await leaderboard_channel.send(
                f"It's {format_time(local_time)}, time to post the weekly leaderboard! The next leaderboard will be posted at {format_time(deadline)}.",
                embed=combo_post,
            )
            thread: Thread = await message.create_thread(
                name=f"{minuend_datetime.date().isoformat()} Weekly Leaderboards"
            )

            for gains_data in leaderboard_data.values():
                embeds = GainsLeaderboardView.get_pages(gains_data)

                for embed in embeds:
                    await thread.send(embed=embed)

    async def _get_gains_leaderboard_data(
        self, guild_id: int, stat: str, subtrahend_datetime: datetime, minuend_datetime: datetime
    ) -> dict:
        async with aiohttp.ClientSession(
            headers={"Authorization": f"Token {TRAINERDEX_API_TOKEN}"}
        ) as session:
            url = URL(
                "https://trainerdex.app/api/v2/leaderboard/?mode=gain&subset=discord&limit=25"
            )
            url %= {
                "guild_id": guild_id,
                "stat": stat,
                "subtrahend_datetime": subtrahend_datetime.isoformat(),
                "minuend_datetime": minuend_datetime.isoformat(),
            }
            async with session.get(url) as response:
                return await response.json()
