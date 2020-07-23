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

from redbot.core import Config
from redbot.core.bot import Red
from redbot.core.utils import chat_formatting

from tdx.core import TrainerDexCore
from tdx.settings import TrainerDexSettings


async def setup(bot: Red) -> None:
    config = Config.get_conf(
        None,
        cog_name='trainerdex',
        identifier=8124637339,  # TrainerDex on a T9 keyboard
        force_registration=True,
    )
    
    config.register_global(**{
        'embed_footer': 'Provided with ❤️ by TrainerDex',
        'notice': chat_formatting.bold("Goals are disabled for now.")+" They're in the middle of being rewritten and I think you'll very much like what I've done with them.\n"+chat_formatting.italics("Sorry for the inconvenience"),
    })
    config.register_guild(**{
        'assign_roles_on_join': True,
        'set_nickname_on_join': True,
        'set_nickname_on_update': True,
        'roles_to_assign_on_approval': {'add': [], 'remove': []},
        'mystic_role': None,
        'valor_role': None,
        'instinct_role': None,
        'tl40_role': None,
    })
    config.register_channel(**{
        'profile_ocr': False,
        'notices': False,
        'post_leaderboard': False,
    })
    
    bot.add_cog(TrainerDexSettings(bot, config))
    cog = TrainerDexCore(bot, config)
    await cog.initialize()
    bot.add_cog(cog)
