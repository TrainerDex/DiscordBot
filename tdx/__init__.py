"""
Official TrainerDex Discord Bot
-------------------------------

TrainerDex cog for Red-DiscordBot 3

:copyright: (c) 2020 JayTurnr
:licence: GNU-GPL3, see LICENSE for more details

"""

__author__ = 'JayTurnr'
__licence__ = 'GNU-GPL'
__copyright__ = 'Copyright 2020 JayTurnr'
__version__ = '1.9.0'

from redbot.core.bot import Red

from tdx.core import TrainerDexCore
from tdx.settings import TrainerDexSettings


async def setup(bot: Red) -> None:
    bot.add_cog(TrainerDexSettings(bot))
    cog = TrainerDexCore(bot)
    await cog.initialize()
    bot.add_cog(cog)
