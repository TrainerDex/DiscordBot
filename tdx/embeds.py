import datetime
import logging
import requests

import discord
from redbot.core import commands
from redbot.core.i18n import Translator, cog_i18n
from redbot.core.utils import chat_formatting

import humanize
import trainerdex
from dateutil.relativedelta import relativedelta, MO

log = logging.getLogger("red.tdx.embeds")
_ = Translator("TrainerDex", __file__)

def check_xp(x: trainerdex.Update) -> int:
    if x.xp is None:
        return 0
    return x.xp


class BaseCard(discord.Embed):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.colour = kwargs.get('colour', kwargs.get('color', 13252437))
        
        self._author = {
            'name': 'TrainerDex',
            'url': 'https://www.trainerdex.co.uk/',
            'icon_url': 'https://www.trainerdex.co.uk/static/img/android-desktop.png',
        }
    
    async def build_card(self, parent, ctx: commands.Context) -> discord.Embed:
        self._parent = parent
        self._ctx = ctx
        
        self._footer = {
            'text': await self._parent.config.embed_footer()
        }
        
        notice = await self._parent.config.notice()
        if notice:
            notice = chat_formatting.info(notice)
            
            if self.description:
                self.description = "{}\n\n{}".format(notice, self.description)
            else:
                self.description = notice
        return self


class ProfileCard(BaseCard):
    def __init__(self, trainer: trainerdex.Trainer, **kwargs):
        super().__init__(**kwargs)
        self._trainer = trainer
        self.colour = int(self._trainer.team().colour.replace("#", ""), 16)
        self.title = _("{nickname} | TL{level}").format(nickname=self._trainer.username, level=self._trainer.level.level)
        self.url = 'https://www.trainerdex.co.uk/profile?id={}'.format(self._trainer.id)
        if self._trainer.update:
            self.timestamp = self._trainer.update.update_time
    
    async def build_card(self, parent, ctx: commands.Context) -> discord.Embed:
        await super().build_card(parent, ctx)
        self.add_field(name=_("Team"), value=self._trainer.team().name)
        self.add_field(name=_("Level"), value=self._trainer.level.level)
        self.add_field(name=_("Total XP"), value=chat_formatting.humanize_number(max(self._trainer.updates(), key=check_xp).xp))
        return self
    
    async def add_guild_leaderboard(self) -> None:
        if self._ctx.guild:
            try:
                guild_leaderboard = self._parent.client.get_discord_leaderboard(self._ctx.guild.id)
            except requests.exceptions.HTTPError as e:
                log.error(e)
            else:
                try:
                    guild_leaderboard = guild_leaderboard.filter_trainers([self._trainer.id])[0].position
                    self.insert_field_at(
                        index = 0,
                        name = _("{guild} Leaderboard").format(guild=self._ctx.guild.name),
                        value = str(guild_leaderboard),
                    )
                except LookupError:
                    pass
    
    async def add_leaderboard(self) -> None:
        try:
            leaderboard = self._parent.client.get_worldwide_leaderboard()
        except requests.exceptions.HTTPError as e:
            log.error(e)
            return
        else:
            try:
                leaderboard = leaderboard.filter_trainers([self._trainer.id])[0].position
                self.insert_field_at(
                    index = 0,
                    name = _("Global Leaderboard"),
                    value = str(leaderboard),
                )
            except LookupError:
                pass


class UpdatedProfileCard(ProfileCard):
    def __init__(self, trainer: trainerdex.Trainer, **kwargs):
        super().__init__(trainer, **kwargs)
        self._alpha = max(self._trainer.updates(), key=check_xp)
        try:
            _updates_before_monday = [x for x in self._trainer.updates() if x.update_time < self._alpha.update_time+relativedelta(weekday=MO(-1), hour=12, minute=0, second=0, microsecond=0)]
            self._beta = max(_updates_before_monday, key=check_xp)
        except ValueError:
            if self._trainer.start_date:
                self._beta = trainerdex.Update({'uuid': None, 'update_time': self._trainer.start_date.isoformat(), 'xp': 0})
                self.description = chat_formatting.info(_("No data old enough found, using actual start date."))
            else:
                self._beta = trainerdex.Update({'uuid': None, 'update_time': datetime.date(2016, 7, 14).isoformat(), 'xp': 0})
                self.description = chat_formatting.info(_("No data old enough found, using assumed start date."))
            
        self.timestamp = self._alpha.update_time
    
    async def build_card(self, parent, ctx: commands.Context) -> discord.Embed:
        await super().build_card(parent, ctx)
        stat_delta = self._alpha.xp - self._beta.xp
        time_delta = self._alpha.update_time - self._beta.update_time
        self.add_field(name=_("XP Gain"), value=_("{gain} over {time}").format(gain=chat_formatting.humanize_number(stat_delta), time=humanize.naturaldelta(time_delta)))
        days = round(time_delta.total_seconds()/86400)
        self.add_field(name=_("Daily XP Gain"), value=_("{gain}/day").format(gain=chat_formatting.humanize_number(round(stat_delta/days))))
        return self
