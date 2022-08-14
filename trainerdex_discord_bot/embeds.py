from __future__ import annotations

import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Union

from humanize import naturaldelta
from discord.channel import TextChannel
from discord.colour import Colour
from discord.commands import ApplicationContext
from discord.embeds import Embed, EmptyEmbed
from discord.guild import Guild
from discord.message import Message
from trainerdex.update import Update

from trainerdex_discord_bot.constants import (
    TRAINERDEX_COLOUR,
    WEBSITE_DOMAIN,
    CustomEmoji,
)
from trainerdex_discord_bot.utils import chat_formatting

if TYPE_CHECKING:
    from trainerdex.leaderboard import GuildLeaderboard, Leaderboard, LeaderboardEntry
    from trainerdex.trainer import Trainer

    from trainerdex_discord_bot.datatypes import Common, GlobalConfig


class BaseCard(Embed):
    async def __new__(cls, *args, **kwargs) -> BaseCard:
        instance = super().__new__(cls)
        await instance.__init__(*args, **kwargs)
        return instance

    async def __init__(
        self,
        common: Common,
        ctx: ApplicationContext,
        /,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        global_config: GlobalConfig = await common.config.get_global()
        self.colour: Union[Colour, int] = kwargs.get(
            "colour",
            kwargs.get("color", TRAINERDEX_COLOUR),
        )
        self.title: Union[str, EmptyEmbed] = kwargs.get("title", EmptyEmbed)
        self.type: str = kwargs.get("type", "rich")
        self.url: Union[str, EmptyEmbed] = kwargs.get("url", EmptyEmbed)
        self.description: Union[str, EmptyEmbed] = kwargs.get("description", EmptyEmbed)
        self.timestamp: Union[datetime.datetime, EmptyEmbed] = kwargs.get("timestamp", EmptyEmbed)

        notice: str = global_config.notice
        if notice:
            notice: str = chat_formatting.info(notice)

            if self.description:
                self.description: str = "{}\n\n{}".format(notice, self.description)
            else:
                self.description: str = notice

        # Default _author
        self._footer: dict[str, str] = {
            "text": global_config.embed_footer,
            "icon_url": f"{WEBSITE_DOMAIN}/static/img/android-chrome-512x512.png",
        }

        # Default _author
        self._author: dict[str, str] = {
            "name": "TrainerDex",
            "url": f"{WEBSITE_DOMAIN}/",
            "icon_url": f"{WEBSITE_DOMAIN}/static/img/android-chrome-512x512.png",
        }

        self._message: Message = ctx.interaction.message
        self._channel: TextChannel = ctx.interaction.channel
        self._guild: Guild = ctx.interaction.guild
        self._common: Common = common


class ProfileCard(BaseCard):
    async def __init__(
        self,
        common: Common,
        ctx: ApplicationContext,
        /,
        *,
        trainer: Trainer,
        update: Update = None,
        **kwargs,
    ):
        await super().__init__(common, ctx, **kwargs)
        self.trainer: Trainer = trainer
        await self.trainer.fetch_updates()
        self.update: Update = update or self.trainer.get_latest_update_for_stat("total_xp")

        self.colour: int = self.trainer.team.colour
        self.title: str = "{nickname} | TL{level}".format(
            nickname=self.trainer.username,
            level=self.trainer.level,
        )
        self.url: str = f"{WEBSITE_DOMAIN}/profile?id={self.trainer.old_id}"
        if self.update:
            self.timestamp: datetime.datetime = self.update.update_time

        self.set_thumbnail(url=f"{WEBSITE_DOMAIN}/static/img/faction/{self.trainer.team.id}.png")

        if self.trainer.trainer_code:
            trainer_code_text: str = f"{CustomEmoji.ADD_FRIEND.value} {self.trainer.trainer_code}"

            if self.description:
                self.description = "\n".join([self.description, trainer_code_text])
            else:
                self.description = trainer_code_text

        if self.update.travel_km:
            self.add_field(
                name=f"{CustomEmoji.TRAVEL_KM.value} Distance Walked",
                value=chat_formatting.format_numbers(self.update.travel_km, 1) + " km",
                inline=False,
            )
        if self.update.capture_total:
            self.add_field(
                name=f"{CustomEmoji.CAPTURE_TOTAL.value} Pokémon Caught",
                value=chat_formatting.format_numbers(self.update.capture_total),
                inline=False,
            )
        if self.update.pokestops_visited:
            self.add_field(
                name=f"{CustomEmoji.POKESTOPS_VISITED.value} PokéStops Visited",
                value=chat_formatting.format_numbers(self.update.pokestops_visited),
                inline=False,
            )
        if self.update.total_xp:
            self.add_field(
                name=f"{CustomEmoji.TOTAL_XP.value} Total XP",
                value=chat_formatting.format_numbers(self.update.total_xp),
                inline=False,
            )
        if self.update.gymbadges_gold:
            self.add_field(
                name=f"{CustomEmoji.GYMBADGES_GOLD.value} Gold Gyms",
                value=chat_formatting.format_numbers(self.update.gymbadges_gold),
                inline=False,
            )

    async def add_guild_leaderboard(self, guild: Guild) -> None:
        entries: list[str] = []
        stats: list[str] = [
            "badge_travel_km",
            "badge_capture_total",
            "badge_pokestops_visited",
            "total_xp",
            "gymbadges_gold",
        ]
        for stat in stats:
            leaderboard: GuildLeaderboard = await self._common.client.get_leaderboard(
                stat=stat, guild=guild
            )
            entry: LeaderboardEntry = await leaderboard.find(
                lambda x: x._trainer_id == self.trainer.old_id
            )
            if entry:
                entries.append(
                    "{} {}".format(
                        CustomEmoji[stat.upper()].value,
                        chat_formatting.format_numbers(entry.position),
                    )
                )
            del leaderboard
            del entry

        if entries:
            self.insert_field_at(
                index=0,
                name=f"{guild.name} Leaderboard (All)",
                value="\n".join(entries),
            )

    async def add_leaderboard(self) -> None:
        entries: list[str] = []
        stats: list[str] = [
            "badge_travel_km",
            "badge_capture_total",
            "badge_pokestops_visited",
            "total_xp",
        ]
        for stat in stats:
            leaderboard: Leaderboard = await self._common.client.get_leaderboard(stat=stat)
            entry: LeaderboardEntry = await leaderboard.find(
                lambda x: x._trainer_id == self.trainer.old_id
            )
            if entry:
                entries.append(
                    "{} {}".format(
                        CustomEmoji[stat.upper()].value,
                        chat_formatting.format_numbers(entry.position),
                    )
                )
            del leaderboard
            del entry

        if entries:
            self.insert_field_at(
                index=0,
                name=f"{CustomEmoji.GLOBAL.value} Leaderboard (Top 1000)",
                value="\n".join(entries),
            )

    async def show_progress(self) -> None:
        this_update: Update = self.update

        if this_update is None:
            return

        window: tuple[datetime.datetime, datetime.datetime] = (
            this_update.update_time - datetime.timedelta(hours=26),
            this_update.update_time,
        )

        stats_to_check: list[str] = [
            x
            for x in [
                "travel_km",
                "capture_total",
                "pokestops_visited",
                "total_xp",
                "gymbadges_gold",
            ]
            if getattr(this_update, x, None) is not None
        ]

        try:
            reference_update: Update = min(
                [
                    x
                    for x in self.trainer.updates
                    if (
                        any([(getattr(x, stat, None) is not None) for stat in stats_to_check])
                        and window[0] < x.update_time < window[1]
                    )
                ],
                key=lambda x: x.update_time,
            )
        except ValueError:
            reference_update = None

        if not reference_update:
            return

        self.clear_fields()
        if not self.description:
            self.description = ""
        self.description += "\nWe're currently trialing a new way to show your progress. The 26-hour window! With achievements!"

        self.add_field(
            name=f"{CustomEmoji.DATE.value} Interval (up to 26 hours)",
            value=naturaldelta(this_update.update_time - reference_update.update_time),
            inline=False,
        )

        TRAVEL_KM_THRESHOLD = Decimal(15)
        TOTAL_XP_THERESHOLD = 250_000
        POKESTOPS_VISITED_THRESHOLD = 50
        CAPTURE_TOTAL_THRESHOLD = 100

        if this_update.travel_km:
            if reference_update.travel_km is not None:
                self.add_field(
                    name=f"{CustomEmoji.TRAVEL_KM.value} Distance Walked",
                    value="+{delta}km ({now}km)\n{award_maybe}".format(
                        now=chat_formatting.format_numbers(this_update.travel_km, 1),
                        delta=chat_formatting.format_numbers(
                            this_update.travel_km - reference_update.travel_km,
                            1,
                        ),
                        award_maybe=(
                            ""
                            if this_update.travel_km < TRAVEL_KM_THRESHOLD
                            else f"🏅 Achieved Thunderlegs (Walk {TRAVEL_KM_THRESHOLD}km)"
                        ),
                    ),
                    inline=False,
                )
            else:
                self.add_field(
                    name=f"{CustomEmoji.TRAVEL_KM.value} Distance Walked",
                    value=chat_formatting.format_numbers(this_update.travel_km) + " km",
                    inline=False,
                )

        if this_update.capture_total:
            if reference_update.capture_total is not None:
                self.add_field(
                    name=f"{CustomEmoji.CAPTURE_TOTAL.value} Pokémon Caught",
                    value="+{delta} ({now})\n{award_maybe}".format(
                        now=chat_formatting.format_numbers(this_update.capture_total, 1),
                        delta=chat_formatting.format_numbers(
                            this_update.capture_total - reference_update.capture_total,
                            1,
                        ),
                        award_maybe=(
                            ""
                            if this_update.capture_total < CAPTURE_TOTAL_THRESHOLD
                            else f"🏅 Achieved Expert Aim (Catch {CAPTURE_TOTAL_THRESHOLD} Pokémon)"
                        ),
                    ),
                    inline=False,
                )
            else:
                self.add_field(
                    name=f"{CustomEmoji.CAPTURE_TOTAL.value} Pokémon Caught",
                    value=chat_formatting.format_numbers(this_update.capture_total),
                    inline=False,
                )

        if this_update.pokestops_visited:
            if reference_update.pokestops_visited is not None:
                self.add_field(
                    name=f"{CustomEmoji.POKESTOPS_VISITED.value} PokéStops Visited",
                    value="+{delta} ({now})\n{award_maybe}".format(
                        now=chat_formatting.format_numbers(this_update.pokestops_visited, 1),
                        delta=chat_formatting.format_numbers(
                            this_update.pokestops_visited - reference_update.pokestops_visited,
                            1,
                        ),
                        award_maybe=(
                            ""
                            if this_update.pokestops_visited < POKESTOPS_VISITED_THRESHOLD
                            else f"🏅 Achieved Explorer (Visit {POKESTOPS_VISITED_THRESHOLD} PokéStops)"
                        ),
                    ),
                    inline=False,
                )
            else:
                self.add_field(
                    name=f"{CustomEmoji.POKESTOPS_VISITED.value} PokéStops Visited",
                    value=chat_formatting.format_numbers(this_update.pokestops_visited),
                    inline=False,
                )

        if this_update.total_xp:
            if reference_update.total_xp is not None:
                self.add_field(
                    name=f"{CustomEmoji.TOTAL_XP.value} Total XP",
                    value="+{delta} ({now})\n{award_maybe}".format(
                        now=chat_formatting.format_numbers(this_update.total_xp, 1),
                        delta=chat_formatting.format_numbers(
                            this_update.total_xp - reference_update.total_xp,
                            1,
                        ),
                        award_maybe=(
                            ""
                            if this_update.total_xp < TOTAL_XP_THERESHOLD
                            else f"🏅 Achieved Dedicated (Earn {TOTAL_XP_THERESHOLD} XP)"
                        ),
                    ),
                    inline=False,
                )
            else:
                self.add_field(
                    name=f"{CustomEmoji.TOTAL_XP.value} Total XP",
                    value=chat_formatting.format_numbers(this_update.total_xp),
                    inline=False,
                )

        if this_update.gymbadges_gold:
            if reference_update.gymbadges_gold is not None:
                self.add_field(
                    name=f"{CustomEmoji.GYMBADGES_GOLD.value} Gold Gyms",
                    value="+{delta} ({now})".format(
                        now=chat_formatting.format_numbers(this_update.gymbadges_gold, 1),
                        delta=chat_formatting.format_numbers(
                            this_update.gymbadges_gold - reference_update.gymbadges_gold,
                            1,
                        ),
                    ),
                    inline=False,
                )
            else:
                self.add_field(
                    name=f"{CustomEmoji.GYMBADGES_GOLD.value} Gold Gyms",
                    value=chat_formatting.format_numbers(this_update.gymbadges_gold),
                    inline=False,
                )
