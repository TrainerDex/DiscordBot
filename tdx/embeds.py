import datetime
import logging
from typing import Dict, List, Union, NoReturn

import discord
from discord.embeds import EmptyEmbed
from redbot.core import commands, Config
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf

import humanize
from tdx import client
from tdx.utils import check_xp
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

    async def __init__(self, ctx: Union[commands.Context, discord.Message], **kwargs) -> None:
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
            "icon_url": "https://www.trainerdex.co.uk/static/img/android-desktop.png",
        }

        # Default _author
        self._author: Dict[str, str] = {
            "name": "TrainerDex",
            "url": "https://www.trainerdex.co.uk/",
            "icon_url": "https://www.trainerdex.co.uk/static/img/android-desktop.png",
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
        self, ctx: Union[commands.Context, discord.Message], trainer: client.Trainer, **kwargs,
    ):
        await super().__init__(ctx, **kwargs)

        self.trainer = trainer

        try:
            self.update = max(self.trainer.updates, key=check_xp)
        except ValueError:
            log.warning("No updates found for {user}".format(user=self.trainer))

        self.colour: int = self.trainer.team.colour
        self.title: str = _("{nickname} | Level {level}").format(
            nickname=self.trainer.username, level=self.trainer.level,
        )
        self.url: str = "https://www.trainerdex.co.uk/profile?id={}".format(self.trainer.old_id)
        if self.trainer.latest_update:
            self.timestamp = self.trainer.latest_update.update_time

        self.add_field(name=_("Team"), value=self.trainer.team)
        self.add_field(name=_("Level"), value=self.trainer.level)
        self.add_field(
            name=_("Total XP"), value=cf.humanize_number(self.trainer.latest_update.total_xp),
        )
        self.set_thumbnail(
            url=f"https://trainerdex.co.uk/static/img/faction/{self.trainer.team.id}.png"
        )

    async def add_guild_leaderboard(self) -> NoReturn:
        raise NotImplementedError

    async def add_leaderboard(self) -> NoReturn:
        raise NotImplementedError

    async def show_progress(self) -> None:
        this_update: client.Update = self.trainer.latest_update

        if this_update is None:
            return

        RRULE = rrule(
            WEEKLY, dtstart=datetime.datetime(2020, 6, 9, 12, 0, tzinfo=UTC), byweekday=MO
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
        else:
            if not self.trainer.start_date:
                return
            last_update: client.PartialUpdate = client.PartialUpdate(
                {
                    "uuid": None,
                    "trainer": self.trainer.old_id,
                    "update_time": getattr(self.trainer, "start_date").isoformat(),
                    "total_xp": 0,
                }
            )
            self.description = cf.info(_("No data old enough found, using start date."))

        stat_delta = this_update.total_xp - last_update.total_xp
        time_delta = this_update.update_time - last_update.update_time
        self.add_field(
            name=_("XP Gain"),
            value=_("{gain} over {time} (since {earlier_date})").format(
                gain=cf.humanize_number(stat_delta),
                time=humanize.naturaldelta(time_delta),
                earlier_date=humanize.naturaldate(last_update.update_time),
            ),
        )
        days: int = round(time_delta.total_seconds() / 86400)
        self.add_field(
            name=_("Daily XP Gain"),
            value=_("{gain}/day").format(gain=cf.humanize_number(round(stat_delta / days))),
        )
