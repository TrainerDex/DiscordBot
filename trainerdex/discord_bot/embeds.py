from __future__ import annotations

import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Union

from dateutil.rrule import rrule
from dateutil.tz import UTC
from discord.channel import TextChannel
from discord.colour import Colour
from discord.commands import ApplicationContext
from discord.embeds import Embed, EmptyEmbed
from discord.guild import Guild
from discord.message import Message
from trainerdex.api.client import TokenClient
from trainerdex.api.update import Update

from trainerdex.discord_bot.constants import (
    TRAINERDEX_COLOUR,
    WEBSITE_DOMAIN,
    CustomEmoji,
)
from trainerdex.discord_bot.utils import chat_formatting
from trainerdex.discord_bot.utils.deadlines import get_last_deadline, get_next_deadline
from trainerdex.discord_bot.utils.general import google_calendar_link_for_datetime

if TYPE_CHECKING:
    from trainerdex.api.leaderboard import (
        GuildLeaderboard,
        Leaderboard,
        LeaderboardEntry,
    )
    from trainerdex.api.trainer import Trainer

    from trainerdex.discord_bot.datatypes import Common, GlobalConfig


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

        self.update: Update = max(self.trainer.updates, key=lambda x: (x.total_xp or 0))
        self.colour: int = self.trainer.team.colour

        try:
            level = await self.trainer.get_level()
        except ValueError:
            self.title: str = self.trainer.username
        else:
             self.title: str = f"{self.trainer.username} | TL{level}"

        self.url: str = f"{WEBSITE_DOMAIN}/profile?id={self.trainer.id}"
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
            async with TokenClient() as client:
                leaderboard: GuildLeaderboard = await client.get_leaderboard(
                    guild=guild,
                    stat=stat,
                )
                entry: LeaderboardEntry = await leaderboard.find(
                    lambda x: x.trainer_id == self.trainer.id
                )
                if entry:
                    entries.append(
                        "{} {}".format(
                            CustomEmoji[stat.upper()].value,
                            chat_formatting.format_numbers(entry.position),
                        )
                    )

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
            async with TokenClient() as client:
                leaderboard: Leaderboard = await client.get_leaderboard(stat=stat)
                entry: LeaderboardEntry = await leaderboard.find(
                    lambda x: x.trainer_id == self.trainer.id
                )
                if entry:
                    entries.append(
                        "{} {}".format(
                            CustomEmoji[stat.upper()].value,
                            chat_formatting.format_numbers(entry.position),
                        )
                    )

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

        last_deadline: datetime.datetime = await get_last_deadline(
            guild_id=(self._guild.id if self._guild else None), now=this_update.update_time
        )
        next_deadline: datetime.datetime = await get_next_deadline(
            guild_id=(self._guild.id if self._guild else None), now=this_update.update_time
        )

        if next_deadline > datetime.datetime.now(tz=datetime.timezone.utc):
            if not self.description:
                self.description = ""
            self.description += "\n\n**Next Deadline:** {} ({}) [[+]]({})".format(
                chat_formatting.format_time(
                    next_deadline, chat_formatting.TimeVerbosity.SHORT_DATETIME
                ),
                chat_formatting.format_time(next_deadline, chat_formatting.TimeVerbosity.DELTA),
                google_calendar_link_for_datetime(next_deadline),
            )

        try:
            last_update: Update = max(
                [
                    x
                    for x in self.trainer.updates
                    if (getattr(x, "total_xp", None) is not None and x.update_time < last_deadline)
                ],
                key=lambda x: x.update_time,
            )
        except ValueError:
            return

        time_delta: datetime.timedelta = this_update.update_time - last_update.update_time
        days: float = max((time_delta.total_seconds() / 86400), 1)

        self.clear_fields()

        self.add_field(
            name=f"{CustomEmoji.DATE.value} Interval",
            value="{then} ⇒ {now} (+{days} days)".format(
                then=chat_formatting.format_time(last_update.update_time),
                now=chat_formatting.format_time(this_update.update_time),
                days=chat_formatting.format_numbers(days),
            ),
            inline=False,
        )
        if this_update.travel_km:
            if last_update.travel_km is not None:
                self.add_field(
                    name=f"{CustomEmoji.TRAVEL_KM.value} Distance Walked",
                    value="{then}km ⇒ {now}km (+{delta} | {daily_gain})".format(
                        then=chat_formatting.format_numbers(last_update.travel_km, 1),
                        now=chat_formatting.format_numbers(this_update.travel_km, 1),
                        delta=chat_formatting.format_numbers(
                            this_update.travel_km - last_update.travel_km,
                            1,
                        ),
                        daily_gain="{gain}/day".format(
                            gain=chat_formatting.format_numbers(
                                (this_update.travel_km - last_update.travel_km) / Decimal(days)
                            )
                            + "km"
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
            if last_update.capture_total is not None:
                self.add_field(
                    name=f"{CustomEmoji.CAPTURE_TOTAL.value} Pokémon Caught",
                    value="{then} ⇒ {now} (+{delta} | {daily_gain})".format(
                        then=chat_formatting.format_numbers(last_update.capture_total),
                        now=chat_formatting.format_numbers(this_update.capture_total),
                        delta=chat_formatting.format_numbers(
                            this_update.capture_total - last_update.capture_total
                        ),
                        daily_gain="{gain}/day".format(
                            gain=chat_formatting.format_numbers(
                                (this_update.capture_total - last_update.capture_total) / days
                            )
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
            if last_update.pokestops_visited is not None:
                self.add_field(
                    name=f"{CustomEmoji.POKESTOPS_VISITED.value} PokéStops Visited",
                    value="{then} ⇒ {now} (+{delta} | {daily_gain})".format(
                        then=chat_formatting.format_numbers(last_update.pokestops_visited),
                        now=chat_formatting.format_numbers(this_update.pokestops_visited),
                        delta=chat_formatting.format_numbers(
                            this_update.pokestops_visited - last_update.pokestops_visited
                        ),
                        daily_gain="{gain}/day".format(
                            gain=chat_formatting.format_numbers(
                                (this_update.pokestops_visited - last_update.pokestops_visited)
                                / days
                            )
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
            if last_update.total_xp is not None:
                self.add_field(
                    name=f"{CustomEmoji.TOTAL_XP.value} Total XP",
                    value="{then} ⇒ {now} (+{delta} | {daily_gain})".format(
                        then=chat_formatting.format_numbers(last_update.total_xp),
                        now=chat_formatting.format_numbers(this_update.total_xp),
                        delta=chat_formatting.format_numbers(
                            this_update.total_xp - last_update.total_xp
                        ),
                        daily_gain="{gain}/day".format(
                            gain=chat_formatting.format_numbers(
                                (this_update.total_xp - last_update.total_xp) / days
                            )
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
            if last_update.gymbadges_gold is not None:
                self.add_field(
                    name=f"{CustomEmoji.GYMBADGES_GOLD.value} Gold Gyms",
                    value="{then} ⇒ {now} (+{delta} | {daily_gain})".format(
                        then=chat_formatting.format_numbers(last_update.gymbadges_gold),
                        now=chat_formatting.format_numbers(this_update.gymbadges_gold),
                        delta=chat_formatting.format_numbers(
                            this_update.gymbadges_gold - last_update.gymbadges_gold
                        ),
                        daily_gain="{gain}/day".format(
                            gain=chat_formatting.format_numbers(
                                (this_update.gymbadges_gold - last_update.gymbadges_gold) / days
                            )
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
