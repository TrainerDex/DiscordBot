import datetime
import logging
import requests
from typing import Dict, List, Union, Optional, NoReturn

import discord
from discord.embeds import EmptyEmbed
from redbot.core import commands, Config
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf

import humanize
import trainerdex
from tdx import converters
from tdx.models import UserData
from tdx.utils import check_xp
from dateutil.relativedelta import relativedelta, MO
from dateutil.rrule import rrule, WEEKLY
from dateutil.tz import UTC

log: logging.Logger = logging.getLogger("red.tdx.embeds")
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
            "name": await config.embed_footer(),
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

        return self


class ProfileCard(BaseCard):
    async def __init__(
        self, ctx: Union[commands.Context, discord.Message], trainer: trainerdex.Trainer, **kwargs,
    ):
        await super().__init__(ctx, **kwargs)

        self.user_data = UserData(
            **{
                "trainer": trainer,
                "team": await converters.TeamConverter().convert(ctx, trainer._get.get("faction")),
                "updates": trainer.updates(),
            }
        )

        try:
            self.user_data.update = max(self.user_data.updates, key=check_xp)
        except ValueError:
            log.warning("No updates found for user {user}".format(user=self.user_data.trainer))

        self.colour: Union[discord.Colour, int] = self.user_data.team.colour
        self.title: str = _("{nickname} | Level {level}").format(
            nickname=self.user_data.trainer.username, level=self.user_data.level.level,
        )
        self.url: str = "https://www.trainerdex.co.uk/profile?id={}".format(
            self.user_data.trainer.id
        )
        if self.user_data.update:
            self.timestamp: datetime.datetime = self.user_data.update.update_time

        self.add_field(name=_("Team"), value=self.user_data.team)
        self.add_field(name=_("Level"), value=self.user_data.level.level)
        self.add_field(
            name=_("Total XP"), value=cf.humanize_number(self.user_data.update.xp),
        )
        return self

    async def add_guild_leaderboard(self) -> NoReturn:
        raise NotImplementedError

    async def add_leaderboard(self) -> NoReturn:
        raise NotImplementedError

    async def show_progress(self) -> None:
        if self.user_data.update is None:
            return

        this_update = self.user_data.update
        RRULE = rrule(
            WEEKLY, dtstart=datetime.datetime(2020, 6, 9, 12, 0, tzinfo=UTC), byweekday=MO
        )
        current_period = (
            RRULE.before(self.user_data.update.update_time, inc=True),
            RRULE.after(self.user_data.update.update_time),
        )
        previous_period = (RRULE.before(current_period[0]), current_period[0])

        queryset: List[trainerdex.Update] = [
            x
            for x in self.user_data.updates
            if (x.update_time < previous_period[1]) and (x.xp is not None)
        ]
        if queryset:
            last_update: trainerdex.Update = max(queryset, key=check_xp)
        else:
            last_update: trainerdex.Update = trainerdex.Update(
                {
                    "uuid": None,
                    "update_time": getattr(
                        self._trainer, "start_date", datetime.date(2016, 7, 14)
                    ).isoformat(),
                    "xp": 0,
                }
            )
            self.description: str = cf.info(_("No data old enough found, using start date."))

        stat_delta: int = this_update.xp - last_update.xp
        time_delta: datetime.timedelta = this_update.update_time - last_update.update_time
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
