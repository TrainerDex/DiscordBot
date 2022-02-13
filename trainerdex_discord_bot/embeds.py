from __future__ import annotations

import datetime
import humanize
import logging
from decimal import Decimal
from dateutil.relativedelta import MO
from dateutil.rrule import WEEKLY, rrule
from dateutil.tz import UTC
from typing import Union, overload

from discord.channel import TextChannel
from discord.commands import ApplicationContext
from discord.colour import Colour
from discord.embeds import Embed, EmptyEmbed
from discord.ext.commands import Bot, Context
from discord.guild import Guild
from discord.message import Message

from trainerdex.client import Client
from trainerdex.leaderboard import Leaderboard, GuildLeaderboard, LeaderboardEntry
from trainerdex.trainer import Trainer
from trainerdex.update import Update
from trainerdex_discord_bot.config import Config
from trainerdex_discord_bot.constants import WEBSITE_DOMAIN, CUSTOM_EMOJI
from trainerdex_discord_bot.datatypes import GlobalConfig
from trainerdex_discord_bot.utils import chat_formatting


logger: logging.Logger = logging.getLogger(__name__)
config: Config = Config()
global_config: GlobalConfig = config.get_global()


class BaseCard(Embed):
    async def __new__(cls, *args, **kwargs) -> BaseCard:
        instance = super().__new__(cls)
        await instance.__init__(*args, **kwargs)
        return instance

    @overload
    async def __init__(self, ctx_or_message: Context | ApplicationContext, /, **kwargs) -> None:
        ...

    @overload
    async def __init__(self, ctx_or_message: Message, bot: Bot, /, **kwargs) -> None:
        ...

    async def __init__(
        self,
        ctx_or_message: Context | Message | ApplicationContext,
        bot: Bot | None = None,
        /,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.colour: Union[Colour, int] = kwargs.get(
            "colour",
            kwargs.get("color", 13252437),
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

        if isinstance(ctx_or_message, Context):
            self._message: Message = ctx_or_message.message
            self._channel: TextChannel = ctx_or_message.channel
            self._guild: Guild = ctx_or_message.guild
            self._bot: Bot = ctx_or_message.bot
        elif isinstance(ctx_or_message, ApplicationContext):
            self._message: Message = ctx_or_message.interaction.message
            self._channel: TextChannel = ctx_or_message.interaction.channel
            self._guild: Guild = ctx_or_message.interaction.guild
            self._bot: Bot = ctx_or_message.bot
        elif isinstance(ctx_or_message, Message):
            self._message: Message = ctx_or_message
            self._channel: TextChannel = ctx_or_message.channel
            self._guild: Guild = ctx_or_message.channel.guild
            self._bot: Bot = bot


class ProfileCard(BaseCard):
    @overload
    async def __init__(
        self,
        ctx_or_message: Context | ApplicationContext,
        /,
        *,
        client: Client,
        trainer: Trainer,
        update: Update = None,
        **kwargs,
    ) -> None:
        ...

    @overload
    async def __init__(
        self,
        ctx_or_message: Message,
        bot: Bot,
        /,
        *,
        client: Client,
        trainer: Trainer,
        update: Update = None,
        **kwargs,
    ) -> None:
        ...

    async def __init__(
        self,
        ctx_or_message: Context | Message | ApplicationContext,
        bot: Bot | None = None,
        /,
        *,
        client: Client,
        trainer: Trainer,
        update: Update = None,
        **kwargs,
    ):
        await super().__init__(ctx_or_message, bot, **kwargs)
        self.client: Client = client
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
            trainer_code_text: str = (
                f"{bot.get_emoji(CUSTOM_EMOJI.ADD_FRIEND.value)} {self.trainer.trainer_code}"
            )

            if self.description:
                self.description = "\n".join([self.description, trainer_code_text])
            else:
                self.description = trainer_code_text

        if self.update.travel_km:
            self.add_field(
                name=f"{bot.get_emoji(CUSTOM_EMOJI.TRAVEL_KM.value)} Distance Walked",
                value=humanize.intcomma(self.update.travel_km) + " km",
                inline=False,
            )
        if self.update.capture_total:
            self.add_field(
                name=f"{bot.get_emoji(CUSTOM_EMOJI.CAPTURE_TOTAL.value)} Pokémon Caught",
                value=humanize.intcomma(self.update.capture_total),
                inline=False,
            )
        if self.update.pokestops_visited:
            self.add_field(
                name=f"{bot.get_emoji(CUSTOM_EMOJI.POKESTOPS_VISITED.value)} PokéStops Visited",
                value=humanize.intcomma(self.update.pokestops_visited),
                inline=False,
            )
        if self.update.total_xp:
            self.add_field(
                name=f"{bot.get_emoji(CUSTOM_EMOJI.TOTAL_XP.value)} Total XP",
                value=humanize.intcomma(self.update.total_xp),
                inline=False,
            )
        if self.update.gymbadges_gold:
            self.add_field(
                name=f"{bot.get_emoji(CUSTOM_EMOJI.GYMBADGES_GOLD.value)} Gold Gyms",
                value=humanize.intcomma(self.update.gymbadges_gold),
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
            leaderboard: GuildLeaderboard = await self.client.get_leaderboard(
                stat=stat, guild=guild
            )
            entry: LeaderboardEntry = await leaderboard.find(
                lambda x: x._trainer_id == self.trainer.old_id
            )
            if entry:
                entries.append(
                    f"{self.bot.get_emoji(getattr(CUSTOM_EMOJI, stat.upper()).value)} {entry.position:,} / {len(leaderboard):,}"
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
            leaderboard: Leaderboard = await self.client.get_leaderboard(stat=stat)
            entry: LeaderboardEntry = await leaderboard.find(
                lambda x: x._trainer_id == self.trainer.old_id
            )
            if entry:
                entries.append(
                    f"{self.bot.get_emoji(getattr(CUSTOM_EMOJI, stat.upper()).value)} {entry.position:,}"
                )
            del leaderboard
            del entry

        if entries:
            self.insert_field_at(
                index=0,
                name=f"{self.bot.get_emoji(CUSTOM_EMOJI.GLOBAL.value)} Leaderboard (Top 1000)",
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
            name=f"{self.bot.get_emoji(CUSTOM_EMOJI.DATE.value)} Interval",
            value="{then} ⇒ {now} (+{days} days)".format(
                then=humanize.naturaldate(last_update.update_time),
                now=humanize.naturaldate(this_update.update_time),
                days=humanize.intcomma(days),
            ),
            inline=False,
        )
        if this_update.travel_km:
            if last_update.travel_km is not None:
                self.add_field(
                    name=f"{self.bot.get_emoji(CUSTOM_EMOJI.TRAVEL_KM.value)} Distance Walked",
                    value="{then}km ⇒ {now}km (+{delta} | {daily_gain})".format(
                        then=humanize.intcomma(last_update.travel_km),
                        now=humanize.intcomma(this_update.travel_km),
                        delta=humanize.intcomma(this_update.travel_km - last_update.travel_km),
                        daily_gain="{gain}/day".format(
                            gain=humanize.intcomma(
                                (this_update.travel_km - last_update.travel_km) / Decimal(days)
                            )
                            + "km"
                        ),
                    ),
                    inline=False,
                )
            else:
                self.add_field(
                    name=f"{self.bot.get_emoji(CUSTOM_EMOJI.TRAVEL_KM.value)} Distance Walked",
                    value=humanize.intcomma(this_update.travel_km) + " km",
                    inline=False,
                )
        if this_update.capture_total:
            if last_update.capture_total is not None:
                self.add_field(
                    name=f"{self.bot.get_emoji(CUSTOM_EMOJI.CAPTURE_TOTAL.value)} Pokémon Caught",
                    value="{then} ⇒ {now} (+{delta} | {daily_gain})".format(
                        then=humanize.intcomma(last_update.capture_total),
                        now=humanize.intcomma(this_update.capture_total),
                        delta=humanize.intcomma(
                            this_update.capture_total - last_update.capture_total
                        ),
                        daily_gain="{gain}/day".format(
                            gain=humanize.intcomma(
                                (this_update.capture_total - last_update.capture_total) / days
                            )
                        ),
                    ),
                    inline=False,
                )
            else:
                self.add_field(
                    name=f"{self.bot.get_emoji(CUSTOM_EMOJI.CAPTURE_TOTAL.value)} Pokémon Caught",
                    value=humanize.intcomma(this_update.capture_total),
                    inline=False,
                )
        if this_update.pokestops_visited:
            if last_update.pokestops_visited is not None:
                self.add_field(
                    name=f"{self.bot.get_emoji(CUSTOM_EMOJI.POKESTOPS_VISITED.value)} PokéStops Visited",
                    value="{then} ⇒ {now} (+{delta} | {daily_gain})".format(
                        then=humanize.intcomma(last_update.pokestops_visited),
                        now=humanize.intcomma(this_update.pokestops_visited),
                        delta=humanize.intcomma(
                            this_update.pokestops_visited - last_update.pokestops_visited
                        ),
                        daily_gain="{gain}/day".format(
                            gain=humanize.intcomma(
                                (this_update.pokestops_visited - last_update.pokestops_visited)
                                / days
                            )
                        ),
                    ),
                    inline=False,
                )
            else:
                self.add_field(
                    name=f"{self.bot.get_emoji(CUSTOM_EMOJI.POKESTOPS_VISITED.value)} PokéStops Visited",
                    value=humanize.intcomma(this_update.pokestops_visited),
                    inline=False,
                )
        if this_update.total_xp:
            if last_update.total_xp is not None:
                self.add_field(
                    name=f"{self.bot.get_emoji(CUSTOM_EMOJI.TOTAL_XP.value)} Total XP",
                    value="{then} ⇒ {now} (+{delta} | {daily_gain})".format(
                        then=humanize.intcomma(last_update.total_xp),
                        now=humanize.intcomma(this_update.total_xp),
                        delta=humanize.intcomma(this_update.total_xp - last_update.total_xp),
                        daily_gain="{gain}/day".format(
                            gain=humanize.intcomma(
                                (this_update.total_xp - last_update.total_xp) / days
                            )
                        ),
                    ),
                    inline=False,
                )
            else:
                self.add_field(
                    name=f"{self.bot.get_emoji(CUSTOM_EMOJI.TOTAL_XP.value)} Total XP",
                    value=humanize.intcomma(this_update.total_xp),
                    inline=False,
                )
        if this_update.gymbadges_gold:
            if last_update.gymbadges_gold is not None:
                self.add_field(
                    name=f"{self.bot.get_emoji(CUSTOM_EMOJI.GYMBADGES_GOLD.value)} Gold Gyms",
                    value="{then} ⇒ {now} (+{delta} | {daily_gain})".format(
                        then=humanize.intcomma(last_update.gymbadges_gold),
                        now=humanize.intcomma(this_update.gymbadges_gold),
                        delta=humanize.intcomma(
                            this_update.gymbadges_gold - last_update.gymbadges_gold
                        ),
                        daily_gain="{gain}/day".format(
                            gain=humanize.intcomma(
                                (this_update.gymbadges_gold - last_update.gymbadges_gold) / days
                            )
                        ),
                    ),
                    inline=False,
                )
            else:
                self.add_field(
                    name=f"{self.bot.get_emoji(CUSTOM_EMOJI.GYMBADGES_GOLD.value)} Gold Gyms",
                    value=humanize.intcomma(this_update.gymbadges_gold),
                    inline=False,
                )
