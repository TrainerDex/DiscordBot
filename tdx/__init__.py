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
__version__ = "2020.30"

from redbot.core import Config
from redbot.core.bot import Red
from redbot.core.utils import chat_formatting

from tdx.core import TrainerDex
from tdx.settings import Settings
from tdx.quickstart import QuickStart


async def setup(bot: Red) -> None:
    config = Config.get_conf(
        None,
        cog_name="trainerdex",
        identifier=8124637339,  # TrainerDex on a T9 keyboard
        force_registration=True,
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
        **{"profile_ocr": False, "notices": False, "post_leaderboard": False,}
    )

    bot.add_cog(Settings(bot, config))
    bot.add_cog(QuickStart(bot, config))
    cog = TrainerDex(bot, config)
    await cog.initialize()
    bot.add_cog(cog)
