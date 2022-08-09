from __future__ import annotations
from decimal import Decimal

from typing import Iterator, Tuple

from dateutil.parser import parse
from discord import Embed, PartialEmoji

from trainerdex_discord_bot.constants import TRAINERDEX_COLOUR, CustomEmoji, Stats
from trainerdex_discord_bot.utils.chat_formatting import format_numbers, format_time


class GainsLeaderboardView:
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
        leaderboard: dict,
        slice: list[dict],
        page_number: int,
    ) -> Embed:

        stat, stat_name, stat_emoji = cls.get_stat_data(leaderboard.get("stat"))


        if stat == "travel_km":
            f = lambda x: format_numbers(Decimal(x))
        else:
            f = lambda x: format_numbers(int(Decimal(x)))

        embed = Embed(
            title=f"{stat_emoji} {stat_name or stat} Leaderboard for {leaderboard.get('title')}",
            colour=TRAINERDEX_COLOUR,
        )
        if page_number == 1:
            embed.description = """**Weekly gains leaderboard, ranked by rate of change per day.**
            
                **Min Rate**: {rate_min}_/day_
                **Avg Rate**: {rate_avg}_/day_
                **Max Rate**: {rate_max}_/day_
                **Min Change**: {delta_min}
                **Avg Change**: {delta_avg}
                **Max Change**: {delta_max}
                **Sum Change**: {delta_sum}
                """.format(
                rate_avg=f(leaderboard["aggregations"]["average_rate"]),
                rate_min=f(leaderboard["aggregations"]["min_rate"]),
                rate_max=f(leaderboard["aggregations"]["max_rate"]),   
                delta_avg=f(leaderboard["aggregations"]["average_change"]),
                delta_min=f(leaderboard["aggregations"]["min_change"]),
                delta_max=f(leaderboard["aggregations"]["max_change"]),
                delta_sum=f(leaderboard["aggregations"]["sum_change"]),
            )
        else:
            embed.description = ""

        for entry in slice:
            if entry['minuend_datetime'] is not None and entry['subtrahend_datetime'] is not None:
                embed.description += f"""
                **{entry['rank']}**:  **[{entry['username']}](https://trainerdex.app/u/{entry['username']})** gained **{f(entry['difference_value_rate'])}_/day_**
                {f(entry['subtrahend_value'])} → {f(entry['minuend_value'])} (+{f(entry['difference_value'])})
                {format_time(parse(entry['subtrahend_datetime']))} → {format_time(parse(entry['minuend_datetime']))}
                """
            elif entry['minuend_datetime'] is not None and entry['subtrahend_datetime'] is None:
                embed.description += f"\n🆕: **[{entry['username']}](https://trainerdex.app/u/{entry['username']})** submitted {f(entry['minuend_value'])} @ {format_time(parse(entry['minuend_datetime']))}"
        return embed

    @classmethod
    def get_pages(
        cls,
        leaderboard: dict,
    ) -> Iterator[Embed]:
        entries: list[dict] = leaderboard.pop("entries", [])
        filtered_entries: list[dict] = [entry for entry in entries if entry.get("minuend_datetime") is not None]

        chunk_size = 15

        for i in range(0, len(filtered_entries), chunk_size):
            chunk = filtered_entries[i:i + chunk_size]
            yield cls.format_page(leaderboard, chunk, page_number=i // chunk_size + 1)
