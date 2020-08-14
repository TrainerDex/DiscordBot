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

import discord
from redbot.core import commands, Config
from redbot.core.bot import Red

from .core import TrainerDex
from .settings import Settings


async def setup(bot: Red) -> None:
    config: Config = Config.get_conf(
        None, cog_name="trainerdex", identifier=8124637339, force_registration=True,
    )

    config.register_global(**{"embed_footer": "Provided with ❤️ by TrainerDex", "notice": None})
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
            "introduction_note": None,
        }
    )
    config.register_channel(**{"profile_ocr": False, "post_leaderboard": False})

    emoji = {
        "teamless": bot.get_emoji(743873748029145209),
        "mystic": bot.get_emoji(430113444558274560),
        "valor": bot.get_emoji(430113457149575168),
        "instinct": bot.get_emoji(430113431333371924),
        "travel_km": bot.get_emoji(743122298126467144),
        "capture_total": bot.get_emoji(743122649529450566),
        "pokestops_visited": bot.get_emoji(743122864303243355),
        "total_xp": bot.get_emoji(743121748630831165),
        "gift": bot.get_emoji(743120044615270616),
        "add_friend": bot.get_emoji(743853499170947234),
        "previous": bot.get_emoji(729769958652772505),
        "next": bot.get_emoji(729770058099982347),
        "loading": bot.get_emoji(471298325904359434),
        "global": bot.get_emoji(743853198217052281),
        "gym": bot.get_emoji(743874196639056096),
        "gym_badge": bot.get_emoji(743853262469333042),
        "number": "#",
        "profile": bot.get_emoji(743853381919178824),
        "date": bot.get_emoji(743874800547791023),
    }

    bot.add_cog(Settings(bot, config))
    cog: commands.Cog = TrainerDex(bot, config, emoji=emoji)
    await cog.initialize()
    bot.add_cog(cog)
    await bot.change_presence(activity=discord.Game(name=__version__))
