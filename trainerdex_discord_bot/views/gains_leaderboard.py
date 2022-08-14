from __future__ import annotations
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

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

    @staticmethod
    def format_numbers(stat: str, number: Decimal) -> str:
        if stat == "travel_km":
            return format_numbers(Decimal(number))
        else:
            return format_numbers(int(Decimal(number)))
        
    @classmethod
    def format_page(
        cls,
        leaderboard: dict,
        slice: list[dict],
        page_number: int,
    ) -> Embed:

        stat_slug, stat_name, stat_emoji = cls.get_stat_data(leaderboard.get("stat"))

        embed = Embed(
            title=f"{stat_emoji} {stat_name or stat_slug} Leaderboard",
            colour=TRAINERDEX_COLOUR,
        )
        embed.timestamp = parse(leaderboard.get("generated_datetime"))
        if page_number == 1:
            embed.description = "\n".join(
                [
                    "**Min Rate**: {rate_min}_/day_",
                    "**Avg Rate**: {rate_avg}_/day_",
                    "**Max Rate**: {rate_max}_/day_",
                    "**Min Change**: {delta_min}",
                    "**Avg Change**: {delta_avg}",
                    "**Max Change**: {delta_max}",
                    "**Sum Change**: {delta_sum}",
                ]
            ).format(
                rate_avg=cls.format_numbers(stat_slug, leaderboard["aggregations"]["average_rate"]),
                rate_min=cls.format_numbers(stat_slug, leaderboard["aggregations"]["min_rate"]),
                rate_max=cls.format_numbers(stat_slug, leaderboard["aggregations"]["max_rate"]),
                delta_avg=cls.format_numbers(stat_slug, leaderboard["aggregations"]["average_change"]),
                delta_min=cls.format_numbers(stat_slug, leaderboard["aggregations"]["min_change"]),
                delta_max=cls.format_numbers(stat_slug, leaderboard["aggregations"]["max_change"]),
                delta_sum=cls.format_numbers(stat_slug, leaderboard["aggregations"]["sum_change"]),
            )
        else:
            embed.description = ""

        for entry in slice:
            if entry["minuend_datetime"] is not None and entry["subtrahend_datetime"] is not None:
                embed.description += "\n".join(
                    [
                        "",
                        f"**{entry['rank']}**:  **[{entry['username']}](https://trainerdex.app/u/{entry['username']})** gained **{cls.format_numbers(stat_slug, entry['difference_value_rate'])}_/day_**",
                        f"{cls.format_numbers(stat_slug, entry['subtrahend_value'])} → {cls.format_numbers(stat_slug, entry['minuend_value'])} (+{cls.format_numbers(stat_slug, entry['difference_value'])})",
                        f"{format_time(parse(entry['subtrahend_datetime']))} → {format_time(parse(entry['minuend_datetime']))}",
                    ]
                )
            elif entry["minuend_datetime"] is not None and entry["subtrahend_datetime"] is None:
                embed.description += f"\n🆕: **[{entry['username']}](https://trainerdex.app/u/{entry['username']})** submitted {cls.format_numbers(stat_slug, entry['minuend_value'])} @ {format_time(parse(entry['minuend_datetime']))}"
        return embed

    @classmethod
    def format_combo_embed(cls, leaderboards: dict[Stats, dict], date_: datetime) -> Embed:
        embed: Embed = Embed(
            title=f"{format_time(date_)} Weekly Leaderboards",
            description="Weekly gains leaderboard, ranked by rate of change per day.",
            colour=TRAINERDEX_COLOUR,
        )
        embed.timestamp = date_

        for stat, data in leaderboards.items():

            stat_slug, stat_name, stat_emoji = cls.get_stat_data(stat.value[0])
            if cls._gains_new_entries(data):
                embed.add_field(
                    name=f"{stat_emoji} {stat_name or stat_slug}",
                    value=cls._make_leaderboard_field(data),
                )

        if embed.fields:
            return embed
        else:
            embed.description = "No new entries to display!"
            return embed

    @staticmethod
    def _gains_new_entries(data: dict) -> list[dict]:
        if data["count"]:
            return [x for x in data["entries"] if x["rank"] is not None]
        return []

    @classmethod
    def _make_leaderboard_field(cls, data: dict) -> str:
        top_5 = data["entries"][:5]
        lines = []
        for entry in top_5:
            rate = cls.format_numbers(data['stat'], entry['difference_value_rate'])
            if Decimal(rate.replace(",", "")) > Decimal("0.00"):
                lines.append(f"**{entry['rank']}**:  **[{entry['username']}](https://trainerdex.app/u/{entry['username']})** - **{rate}_/day_**")

        return "\n".join(lines)

    @classmethod
    def get_pages(
        cls,
        leaderboard: dict,
    ) -> Iterator[Embed]:
        entries: list[dict] = leaderboard.pop("entries", [])
        filtered_entries: list[dict] = [
            entry for entry in entries if entry.get("minuend_datetime") is not None
        ]

        chunk_size = 15

        for i in range(0, len(filtered_entries), chunk_size):
            chunk = filtered_entries[i : i + chunk_size]
            yield cls.format_page(leaderboard, chunk, page_number=i // chunk_size + 1)
