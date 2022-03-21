import asyncio
import logging
import os

from discord import Game, Intents, Message
from discord.ext.commands import Bot
from trainerdex.client import Client

from trainerdex_discord_bot import __version__
from trainerdex_discord_bot.cogs.interface import Cog
from trainerdex_discord_bot.config import Config
from trainerdex_discord_bot.constants import (
    DEBUG,
    DEBUG_GUILDS,
    DEFAULT_PREFIX,
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
intents = Intents.default()
intents.members = True
intents.message_content = True


bot: Bot = Bot(
    debug_guilds=DEBUG_GUILDS if DEBUG else None,
    description="TrainerDex, a Discord bot for Pokemon Go.",
    case_insensitive=True,
    command_prefix=get_prefix,
    intents=intents,
    strip_after_prefix=True,  # Set true as iPhone is a bitch.
    loop=loop,
)
logger.info("Pycord initialized.")


@bot.event
async def on_ready() -> None:
    logger.info(
        "Bot ready! Logged in as %(user)s (%(user_id)s). %(num_guilds)s guilds.",
        {
            "user": bot.user,
            "user_id": bot.user.id,
            "num_guilds": len(bot.guilds),
        },
    )
    await set_presence_to_version(bot)
    app_info = await bot.application_info()
    logger.info(
        "Bot %(name)s hosted by %(owner)s (%(owner_id)s), created by @TurnrDev.",
        {
            "name": app_info.name,
            "owner": (app_info.team and f"{app_info.team.name} Team") or app_info.owner,
            "owner_id": (app_info.team and app_info.team.id) or app_info.owner.id,
        },
    )
    logger.info("Public: %(public)s", {"public": app_info.bot_public})


logger.info("Initializing TrainerDex API Client...")
client: Client = Client(token=TRAINERDEX_API_TOKEN, loop=loop)
logger.info("Pycord initialized.")


# Construct Common dataclass
common: Common = Common(
    bot=bot,
    config=config,
    client=client,
)


logger.info("Loading cogs...")
for cog in Cog.__subclasses__():
    bot.add_cog(cog(common))

try:
    logger.info("Running bot...")
    loop.run_until_complete(bot.start(os.environ["DISCORD_TOKEN"]))
except KeyboardInterrupt:
    loop.run_until_complete(bot.close())
finally:
    loop.close()
