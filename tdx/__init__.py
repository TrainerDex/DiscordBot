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
__version__ = "2020.31.2"

import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.utils import chat_formatting

from tdx.core import TrainerDex
from tdx.settings import Settings


async def setup(bot: Red) -> None:
    config: Config = Config.get_conf(
        None, cog_name="trainerdex", identifier=8124637339, force_registration=True,
    )

    config.register_global(
        **{
            "embed_footer": "Provided with ❤️ by TrainerDex",
            "notice": chat_formatting.bold("Leaderboards are disabled for now.")
            + " There's a weird bug. I'm working on it.\n"
            + chat_formatting.italics("Sorry for the inconvenience"),
        }
    )
    config.register_guild(
        **{
            "assign_roles_on_join": True,
            "set_nickname_on_join": True,
            "set_nickname_on_update": True,
            "roles_to_assign_on_approval": {"add": [], "remove": []},
            "mystic_role": None,
            "valor_role": None,
            "instinct_role": None,
            "tl40_role": None,
        }
    )
    config.register_channel(
        **{"profile_ocr": False, "post_leaderboard": False,}
    )

    bot.add_cog(Settings(bot, config))
    cog: commands.Cog = TrainerDex(bot, config)
    await cog.initialize()
    bot.add_cog(cog)
    await bot.change_presence(activity=discord.Game(name=__version__))
