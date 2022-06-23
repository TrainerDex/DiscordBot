from __future__ import annotations

from typing import List, Tuple

import humanize
from discord import ApplicationContext, Embed, PartialEmoji
from discord.ext.pages.pagination import Paginator
from aiostream import stream

from trainerdex.leaderboard import BaseLeaderboard, GuildLeaderboard, LeaderboardEntry
from trainerdex_discord_bot.constants import TRAINERDEX_COLOUR, CustomEmoji, Stats
from trainerdex_discord_bot.utils.chat_formatting import format_numbers


class LeaderboardView(Paginator):
    @classmethod
    async def create(
        cls,
        ctx: ApplicationContext,
        leaderboard_data: BaseLeaderboard,
        *args,
        **kwargs,
    ):
        pages = await cls.get_pages(ctx, leaderboard_data)
        return cls(pages, disable_on_timeout=True)

    @staticmethod
    def get_stat_data(stat: str) -> Tuple[str, str | None, PartialEmoji | None]:
        return (
            stat,
            (i.value[1] if (i := Stats.__dict__.get(stat.upper())) else None),
            (i.value if (i := CustomEmoji.__dict__.get(stat.upper())) else None),
        )

    @classmethod
    def format_page(
        cls,
        ctx: ApplicationContext,
        leaderboard: BaseLeaderboard,
        slice: List[LeaderboardEntry],
    ) -> Embed:

        stat, stat_name, stat_emoji = cls.get_stat_data(leaderboard.stat)

        embed = Embed(
            title=f"{stat_emoji} {stat_name or stat} Leaderboard",
            description=(
                """{trainer_emoji} Trainer Count: {stat_count}
                {stat_emoji} Min: {stat_min}
                {stat_emoji} Avg: {stat_avg}
                {stat_emoji} Max: {stat_max}
                {stat_emoji} Sum: {stat_sum}"""
            ).format(
                trainer_emoji=CustomEmoji.ADD_FRIEND.value,
                stat_emoji=stat_emoji,
                stat_avg=format_numbers(leaderboard.avg),
                stat_count=format_numbers(leaderboard.count),
                stat_sum=format_numbers(leaderboard.sum),
                stat_min=format_numbers(leaderboard.min),
                stat_max=format_numbers(leaderboard.max),
            ),
            colour=TRAINERDEX_COLOUR,
        )

        if isinstance(leaderboard, GuildLeaderboard):
            embed.set_author(
                name=ctx.interaction.guild.name, icon_url=ctx.interaction.guild.icon.url
            )

        for entry in slice:
            team_emoji = getattr(
                CustomEmoji, entry.faction.verbose_name.upper(), CustomEmoji.TRAINERDEX
            ).value
            embed.add_field(
                name=f"{team_emoji} {entry.position} {entry.username}",
                value=f"- {format_numbers(entry.value)} • {humanize.naturaldate(entry.last_updated)}",
                inline=False,
            )
        return embed

    @classmethod
    async def get_pages(
        cls,
        ctx: ApplicationContext,
        leaderboard: BaseLeaderboard,
    ) -> List[Embed]:
        embeds = []
        async for chunk in stream.chunks(leaderboard, 10):
            embeds.append(cls.format_page(ctx, leaderboard, chunk))
        return embeds