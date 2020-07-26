import datetime
import logging
import requests
from typing import Dict, Union, Optional, NoReturn

import discord
from redbot.core import commands
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf

import humanize
import trainerdex
from tdx.utils import check_xp
from dateutil.relativedelta import relativedelta, MO

log: logging.Logger = logging.getLogger("red.tdx.embeds")
_ = Translator("TrainerDex", __file__)


class BaseCard(discord.Embed):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.colour: Union[discord.Colour, int] = kwargs.get(
            "colour", kwargs.get("color", 13252437)
        )

        self._author: Dict = {
            "name": "TrainerDex",
            "url": "https://www.trainerdex.co.uk/",
            "icon_url": "https://www.trainerdex.co.uk/static/img/android-desktop.png",
        }

    async def build_card(
        self, parent, ctx: Union[commands.Context, discord.Message]
    ) -> discord.Embed:
        self._parent = parent

        if isinstance(ctx, commands.Context):
            self._message: discord.Message = ctx.message
            self._channel: discord.TextChannel = ctx.channel
            self._guild: discord.Guild = ctx.guild
        elif isinstance(ctx, discord.Message):
            self._message: discord.Message = ctx
            self._channel: discord.TextChannel = ctx.channel
            self._guild: discord.Guild = ctx.channel.guild

        self._footer: Dict = {"text": await self._parent.config.embed_footer()}

        notice: Optional[str] = await self._parent.config.notice()
        if notice:
            notice: str = cf.info(notice)

            if self.description:
                self.description: str = "{}\n\n{}".format(notice, self.description)
            else:
                self.description: str = notice
        return self


class ProfileCard(BaseCard):
    def __init__(self, trainer: trainerdex.Trainer, **kwargs):
        super().__init__(**kwargs)
        self._trainer: trainerdex.Trainer = trainer
        self.colour: Union[discord.Colour, int] = int(
            self._trainer.team().colour.replace("#", ""), 16
        )
        self.title: str = _("{nickname} | Level {level}").format(
            nickname=self._trainer.username, level=self._trainer.level.level
        )
        self.url: str = "https://www.trainerdex.co.uk/profile?id={}".format(self._trainer.id)
        if self._trainer.update:
            self.timestamp: datetime.datetime = self._trainer.update.update_time

    async def build_card(self, parent, ctx: commands.Context) -> discord.Embed:
        await super().build_card(parent, ctx)
        self.add_field(name=_("Team"), value=self._trainer.team().name)
        self.add_field(name=_("Level"), value=self._trainer.level.level)
        self.add_field(
            name=_("Total XP"),
            value=cf.humanize_number(max(self._trainer.updates(), key=check_xp).xp),
        )
        return self

    async def add_guild_leaderboard(self) -> NoReturn:
        raise NotImplementedError

    async def add_leaderboard(self) -> NoReturn:
        raise NotImplementedError

    async def show_progress(self) -> None:
        self._alpha: Optional[trainerdex.Update] = max(self._trainer.updates(), key=check_xp)
        try:
            _updates_before_monday: List[trainerdex.Update] = [
                x
                for x in self._trainer.updates()
                if x.update_time
                < self._alpha.update_time
                + relativedelta(weekday=MO(-1), hour=12, minute=0, second=0, microsecond=0)
            ]
            self._beta: Optional[trainerdex.Update] = max(_updates_before_monday, key=check_xp)
        except ValueError:
            self._beta: trainerdex.Update = trainerdex.Update(
                {
                    "uuid": None,
                    "update_time": getattr(
                        self._trainer, "start_date", datetime.date(2016, 7, 14)
                    ).isoformat(),
                    "xp": 0,
                }
            )
            self.description: str = cf.info(_("No data old enough found, using start date."))

        self.timestamp: datetime.datetime = self._alpha.update_time
        stat_delta: int = self._alpha.xp - self._beta.xp
        time_delta: datetime.timedelta = self._alpha.update_time - self._beta.update_time
        self.add_field(
            name=_("XP Gain"),
            value=_("{gain} over {time} (since {earlier_date})").format(
                gain=cf.humanize_number(stat_delta),
                time=humanize.naturaldelta(time_delta),
                earlier_date=self._beta.update_time,
            ),
        )
        days: int = round(time_delta.total_seconds() / 86400)
        self.add_field(
            name=_("Daily XP Gain"),
            value=_("{gain}/day").format(gain=cf.humanize_number(round(stat_delta / days))),
        )
