import logging
import os
from discord import Message
from discord.ext.commands import Bot
from trainerdex_discord_bot.config import Config
from trainerdex_discord_bot.constants import DEBUG, DEBUG_GUILDS, DEFAULT_PREFIX, DISCORD_OWNER_IDS
from trainerdex_discord_bot.core import TrainerDex

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

logger: logging.Logger = logging.getLogger(__name__)


def get_prefix(bot: Bot, message: Message) -> str:
    config = Config()
    if message.guild:
        return config.get_guild(message.guild).prefix
    return DEFAULT_PREFIX


logger.info("Initializing Pycord...")
bot = Bot(
    debug_guilds=DEBUG_GUILDS if DEBUG else None,
    description="TrainerDex, a Discord bot for Pokemon Go.",
    case_insensitive=True,
    command_prefix=get_prefix,
    strip_after_prefix=True,  # Set true as iPhone is a bitch.
    owner_ids=DISCORD_OWNER_IDS,
)
logger.info("Pycord initialized.")
logger.info("Attaching TrainerDex...")
bot.add_cog(TrainerDex(bot))
logger.info("Running bot...")
bot.run(os.environ["DISCORD_TOKEN"])
