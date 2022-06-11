from __future__ import annotations

import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Union

import humanize
from dateutil.relativedelta import MO
from dateutil.rrule import WEEKLY, rrule
from dateutil.tz import UTC
from discord.channel import TextChannel
from discord.colour import Colour
from discord.commands import ApplicationContext
from discord.embeds import Embed, EmptyEmbed
from discord.guild import Guild
from discord.message import Message
from trainerdex.update import Update

from trainerdex_discord_bot.constants import TRAINERDEX_COLOUR, WEBSITE_DOMAIN, CustomEmoji
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

        RRULE = rrule(
            WEEKLY, dtstart=datetime.datetime(2016, 7, 4, 12, 0, tzinfo=UTC), byweekday=MO
        )

        current_period: tuple[rrule, rrule] = (
            RRULE.before(this_update.update_time, inc=True),
            RRULE.after(this_update.update_time),
        )

        try:
            last_update: Update = max(
                [
                    x
                    for x in self.trainer.updates
                    if (
                        getattr(x, "total_xp", None) is not None
                        and x.update_time < current_period[0]
                    )
                ],
                key=lambda x: x.update_time,
            )
        except ValueError:
            last_update = None

        if not last_update:
            if not self.trainer.start_date:
                return
            last_update: Update = Update(
                conn=None,
                data={
                    "uuid": "00000000-0000-0000-0000-000000000000",
                    "trainer": self.trainer.old_id,
                    "update_time": datetime.datetime(
                        self.trainer.start_date.year,
                        self.trainer.start_date.month,
                        self.trainer.start_date.day,
                        0,
                        0,
                        0,
                        tzinfo=UTC,
                    ).isoformat(),
                    "badge_travel_km": 0,
                    "badge_capture_total": 0,
                    "badge_pokestops_visited": 0,
                    "total_xp": 0,
                },
            )
            data_inacuracy_notice: str = chat_formatting.info(
                "No data old enough found, using start date."
            )
            if self.description:
                self.description = "\n".join([self.description, data_inacuracy_notice])
            else:
                self.description = data_inacuracy_notice

        time_delta: datetime.timedelta = this_update.update_time - last_update.update_time
        days: float = max((time_delta.total_seconds() / 86400), 1)

        self.clear_fields()

        self.add_field(
            name=f"{CustomEmoji.DATE.value} Interval",
            value="{then} ⇒ {now} (+{days} days)".format(
                then=humanize.naturaldate(last_update.update_time),
                now=humanize.naturaldate(this_update.update_time),
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
