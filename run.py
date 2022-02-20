import asyncio
import logging
import os
from discord import Game, Message
from discord.ext.commands import Bot

from trainerdex.client import Client
from trainerdex_discord_bot import __version__
from trainerdex_discord_bot.cogs import (
    LeaderboardCog,
    ModCog,
    PostCog,
    ProfileCog,
    SettingsCog,
)
from trainerdex_discord_bot.config import Config
from trainerdex_discord_bot.constants import (
    DEBUG,
    DEBUG_GUILDS,
    DEFAULT_PREFIX,
    DISCORD_OWNER_IDS,
    TRAINERDEX_API_TOKEN,
)
from trainerdex_discord_bot.datatypes import Common

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

logger: logging.Logger = logging.getLogger(__name__)

logger.debug("Initializing Event Loop...")
loop = asyncio.get_event_loop()

logger.info("Initializing Config...")
config: Config = Config()
logger.info("Config initialized.")


async def get_prefix(bot: Bot, message: Message) -> str:
    global config
    if message.guild:
        config = await config.get_guild(message.guild)
        return config.prefix
    return DEFAULT_PREFIX


async def set_presence_to_version(bot: Bot) -> None:
    await bot.wait_until_ready()
    logger.info("Setting presence to version %s...", __version__)
    await bot.change_presence(activity=Game(name=__version__))


logger.info("Initializing Pycord...")
bot: Bot = Bot(
    debug_guilds=DEBUG_GUILDS if DEBUG else None,
    description="TrainerDex, a Discord bot for Pokemon Go.",
    case_insensitive=True,
    command_prefix=get_prefix,
    strip_after_prefix=True,  # Set true as iPhone is a bitch.
    owner_ids=DISCORD_OWNER_IDS,
    loop=loop,
)
logger.info("Pycord initialized.")

logger.info("Initializing TrainerDex API Client...")
client: Client = Client(token=TRAINERDEX_API_TOKEN, loop=loop)
logger.info("Pycord initialized.")

loop.create_task(set_presence_to_version(bot))

# Construct Common dataclass
common: Common = Common(
    bot=bot,
    config=config,
    client=client,
)


logger.info("Loading cogs...")
bot.add_cog(PostCog(common))
bot.add_cog(ProfileCog(common))
bot.add_cog(SettingsCog(common))
bot.add_cog(ModCog(common))
bot.add_cog(LeaderboardCog(common))

try:
    logger.info("Running bot...")
    loop.run_until_complete(bot.start(os.environ["DISCORD_TOKEN"]))
except KeyboardInterrupt:
    loop.run_until_complete(bot.close())
finally:
    loop.close()
