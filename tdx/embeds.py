import datetime
import logging
from typing import Dict, List, Union

import discord
from discord.embeds import EmptyEmbed
from redbot.core import commands, Config
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf

import humanize
import trainerdex as client
from .utils import check_xp, append_icon
from dateutil.relativedelta import MO
from dateutil.rrule import rrule, WEEKLY
from dateutil.tz import UTC

log: logging.Logger = logging.getLogger(__name__)
_ = Translator("TrainerDex", __file__)
config = Config.get_conf(
    None, cog_name="trainerdex", identifier=8124637339, force_registration=True,
)


class BaseCard(discord.Embed):
    async def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        await instance.__init__(*args, **kwargs)
        return instance

    async def __init__(self, ctx: commands.Context, **kwargs) -> None:
        super().__init__(**kwargs)

        # Set default colour to TrainerDex brand colour
        try:
            colour: Union[discord.Colour, int] = kwargs["colour"]
        except KeyError:
            colour: Union[discord.Colour, int] = kwargs.get("color", 13252437)
        self.colour: Union[discord.Colour, int] = colour
        self.title: str = kwargs.get("title", EmptyEmbed)
        self.type: str = kwargs.get("type", "rich")
        self.url: str = kwargs.get("url", EmptyEmbed)
        self.description: str = kwargs.get("description", EmptyEmbed)

        notice: str = await config.notice()
        if notice:
            notice: str = cf.info(notice)

            if self.description:
                self.description: str = "{}\n\n{}".format(notice, self.description)
            else:
                self.description: str = notice

        try:
            timestamp = kwargs["timestamp"]
        except KeyError:
            pass
        else:
            self.timestamp = timestamp

        # Default _author
        self._footer: Dict[str, str] = {
            "text": await config.embed_footer(),
            "icon_url": "https://www.trainerdex.co.uk/static/img/android-chrome-512x512.png",
        }

        # Default _author
        self._author: Dict[str, str] = {
            "name": "TrainerDex",
            "url": "https://www.trainerdex.co.uk/",
            "icon_url": "https://www.trainerdex.co.uk/static/img/android-chrome-512x512.png",
        }

        if isinstance(ctx, commands.Context):
            self._message: discord.Message = ctx.message
            self._channel: discord.TextChannel = ctx.channel
            self._guild: discord.Guild = ctx.guild
        elif isinstance(ctx, discord.Message):
            self._message: discord.Message = ctx
            self._channel: discord.TextChannel = ctx.channel
            self._guild: discord.Guild = ctx.channel.guild


class ProfileCard(BaseCard):
    async def __init__(
        self,
        ctx: commands.Context,
        client: client.Client,
        trainer: client.Trainer,
        emoji: Dict[str, Union[discord.Emoji, str]],
        **kwargs,
    ):
        await super().__init__(ctx, **kwargs)
        self.emoji = emoji
        self.client = client
        self.trainer = trainer
        self.latest_update = await self.trainer.latest_update.upgrade()

        try:
            self.update = max(self.trainer.updates, key=check_xp)
        except ValueError:
            log.warning("No updates found for {user}".format(user=self.trainer))

        self.colour: int = self.trainer.team.colour
        self.title: str = _("{nickname} | TL{level}").format(
            nickname=self.trainer.username, level=self.trainer.level,
        )
        self.url: str = "https://www.trainerdex.co.uk/profile?id={}".format(self.trainer.old_id)
        if self.latest_update:
            self.timestamp = self.latest_update.update_time

        self.set_thumbnail(
            url=f"https://trainerdex.co.uk/static/img/faction/{self.trainer.team.id}.png"
        )

        if self.trainer.trainer_code:
            trainer_code_text = append_icon(
                icon=self.emoji.get("add_friend"), text=f"`{self.trainer.trainer_code}`"
            )

            if self.description:
                self.description = "\n".join([self.description, trainer_code_text])
            else:
                self.description = trainer_code_text

        self.add_field(
            name=append_icon(icon=self.emoji.get("gym"), text=_("Team")),
            value=self.trainer.team.verbose_name,
        )

        if self.latest_update.travel_km:
            self.add_field(
                name=append_icon(icon=self.emoji.get("travel_km"), text=_("Distance Walked")),
                value=cf.humanize_number(self.latest_update.travel_km) + " km",
                inline=False,
            )
        if self.latest_update.capture_total:
            self.add_field(
                name=append_icon(icon=self.emoji.get("capture_total"), text=_("Pokémon Caught")),
                value=cf.humanize_number(self.latest_update.capture_total),
                inline=False,
            )
        if self.latest_update.pokestops_visited:
            self.add_field(
                name=append_icon(
                    icon=self.emoji.get("pokestops_visited"), text=_("PokéStops Visited")
                ),
                value=cf.humanize_number(self.latest_update.pokestops_visited),
                inline=False,
            )
        if self.latest_update.total_xp:
            self.add_field(
                name=append_icon(icon=self.emoji.get("total_xp"), text=_("Total XP")),
                value=cf.humanize_number(self.latest_update.total_xp),
                inline=False,
            )

    async def add_guild_leaderboard(self, guild: discord.Guild) -> None:
        leaderboard = await self.client.get_leaderboard(guild=guild)
        entry = await leaderboard.find(lambda x: x._trainer_id == self.trainer.old_id)
        if entry:
            self.insert_field_at(
                index=0,
                name=append_icon(icon=self.emoji.get("total_xp"), text=_("Leaderboard")),
                value="{:,}/{:,}".format(entry.position, len(leaderboard)),
            )

    async def add_leaderboard(self) -> None:
        leaderboard = await self.client.get_leaderboard()
        entry = await leaderboard.find(lambda x: x._trainer_id == self.trainer.old_id)
        if entry:
            self.insert_field_at(
                index=0,
                name=append_icon(
                    icon=self.emoji.get("global"),
                    text=append_icon(icon=self.emoji.get("total_xp"), text=_("Leaderboard")),
                ),
                value="{:,}/{:,}+".format(entry.position, 9000),
            )

    async def show_progress(self) -> None:

        this_update: client.Update = self.latest_update

        if this_update is None:
            return

        RRULE = rrule(
            WEEKLY, dtstart=datetime.datetime(2016, 7, 4, 12, 0, tzinfo=UTC), byweekday=MO
        )

        current_period = (
            RRULE.before(this_update.update_time, inc=True),
            RRULE.after(this_update.update_time),
        )
        previous_period = (RRULE.before(current_period[0]), current_period[0])

        queryset: List[client.PartialUpdate] = [
            x
            for x in self.trainer.updates
            if (x.update_time < previous_period[1]) and (x.total_xp is not None)
        ]

        if queryset:
            last_update: client.PartialUpdate = max(queryset, key=check_xp)
            last_update: client.Update = await last_update.upgrade()
        else:
            if not self.trainer.start_date:
                return
            last_update: client.Update = client.Update(
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
            data_inacuracy_notice = cf.info(_("No data old enough found, using start date."))
            if self.description:
                self.description = "\n".join([self.description, data_inacuracy_notice])
            else:
                self.description = data_inacuracy_notice

        time_delta = this_update.update_time - last_update.update_time
        days: int = max(round(time_delta.total_seconds() / 86400), 1)

        self.clear_fields()

        self.add_field(
            name=append_icon(icon=self.emoji.get("gym"), text=_("Team")),
            value=self.trainer.team.verbose_name,
        )

        self.add_field(
            name=append_icon(icon=self.emoji.get("date"), text=_("Interval")),
            value="{then} ⇒ {now} (+{delta})".format(
                then=humanize.naturaldate(last_update.update_time),
                now=humanize.naturaldate(this_update.update_time),
                delta=humanize.naturaldelta(time_delta),
            ),
            inline=False,
        )
        if this_update.travel_km:
            if last_update.travel_km is not None:
                self.add_field(
                    name=append_icon(icon=self.emoji.get("travel_km"), text=_("Distance Walked")),
                    value="{then}km ⇒ {now}km (+{delta} | {daily_gain})".format(
                        then=cf.humanize_number(last_update.travel_km),
                        now=cf.humanize_number(this_update.travel_km),
                        delta=cf.humanize_number(this_update.travel_km - last_update.travel_km),
                        daily_gain=_("{gain}/day").format(
                            gain=cf.humanize_number(
                                round((this_update.travel_km - last_update.travel_km) / days)
                            )
                            + "km"
                        ),
                    ),
                    inline=False,
                )
            else:
                self.add_field(
                    name=append_icon(icon=self.emoji.get("travel_km"), text=_("Distance Walked")),
                    value=cf.humanize_number(self.latest_update.travel_km) + " km",
                    inline=False,
                )
        if self.latest_update.capture_total:
            if last_update.capture_total is not None:
                self.add_field(
                    name=append_icon(
                        icon=self.emoji.get("capture_total"), text=_("Pokémon Caught")
                    ),
                    value="{then} ⇒ {now} (+{delta} | {daily_gain})".format(
                        then=cf.humanize_number(last_update.capture_total),
                        now=cf.humanize_number(this_update.capture_total),
                        delta=cf.humanize_number(
                            this_update.capture_total - last_update.capture_total
                        ),
                        daily_gain=_("{gain}/day").format(
                            gain=cf.humanize_number(
                                round(
                                    (this_update.capture_total - last_update.capture_total) / days
                                )
                            )
                        ),
                    ),
                    inline=False,
                )
            else:
                self.add_field(
                    name=append_icon(
                        icon=self.emoji.get("capture_total"), text=_("Pokémon Caught")
                    ),
                    value=cf.humanize_number(self.latest_update.capture_total),
                    inline=False,
                )
        if self.latest_update.pokestops_visited:
            if last_update.pokestops_visited is not None:
                self.add_field(
                    name=append_icon(
                        icon=self.emoji.get("pokestops_visited"), text=_("PokéStops Visited")
                    ),
                    value="{then} ⇒ {now} (+{delta} | {daily_gain})".format(
                        then=cf.humanize_number(last_update.pokestops_visited),
                        now=cf.humanize_number(this_update.pokestops_visited),
                        delta=cf.humanize_number(
                            this_update.pokestops_visited - last_update.pokestops_visited
                        ),
                        daily_gain=_("{gain}/day").format(
                            gain=cf.humanize_number(
                                round(
                                    (this_update.pokestops_visited - last_update.pokestops_visited)
                                    / days
                                )
                            )
                        ),
                    ),
                    inline=False,
                )
            else:
                self.add_field(
                    name=append_icon(
                        icon=self.emoji.get("pokestops_visited"), text=_("PokéStops Visited")
                    ),
                    value=cf.humanize_number(self.latest_update.pokestops_visited),
                    inline=False,
                )
        if self.latest_update.total_xp:
            if last_update.total_xp is not None:
                self.add_field(
                    name=append_icon(icon=self.emoji.get("total_xp"), text=_("Total XP")),
                    value="{then} ⇒ {now} (+{delta} | {daily_gain})".format(
                        then=cf.humanize_number(last_update.total_xp),
                        now=cf.humanize_number(this_update.total_xp),
                        delta=cf.humanize_number(this_update.total_xp - last_update.total_xp),
                        daily_gain=_("{gain}/day").format(
                            gain=cf.humanize_number(
                                round((this_update.total_xp - last_update.total_xp) / days)
                            )
                        ),
                    ),
                    inline=False,
                )
            else:
                self.add_field(
                    name=append_icon(icon=self.emoji.get("total_xp"), text=_("Total XP")),
                    value=cf.humanize_number(self.latest_update.total_xp),
                    inline=False,
                )
