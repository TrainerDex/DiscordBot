"""
Official TrainerDex Discord Bot
-------------------------------

TrainerDex cog for Red-DiscordBot 3

:copyright: (c) 2020 TrainerDex/TurnrDev
:licence: GNU-GPL3, see LICENSE for more details

"""

__author__ = "TurnrDev"
__licence__ = "GNU-GPL"
__copyright__ = "Copyright 2020 TrainerDex/TurnrDev"
__version__ = "2020.34.0a"

from discord import Game
from redbot.core import commands
from redbot.core.bot import Red

from .trainerdex import TrainerDex


async def setup(bot: Red) -> None:
    cog: commands.Cog = TrainerDex(bot)
    await cog.initialize()
    bot.add_cog(cog)
    await bot.change_presence(activity=Game(name=__version__))
