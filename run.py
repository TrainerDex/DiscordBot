import asyncio
import logging
import os
import sys
import traceback

from discord import ApplicationContext, Bot, CheckFailure, Game, Intents
from discord.abc import Messageable
from trainerdex.client import Client

from trainerdex_discord_bot import __version__
from trainerdex_discord_bot.cogs.interface import Cog
from trainerdex_discord_bot.config import Config
from trainerdex_discord_bot.constants import DEBUG, DEBUG_GUILDS, TRAINERDEX_API_TOKEN
from trainerdex_discord_bot.datatypes import Common
from trainerdex_discord_bot.utils import chat_formatting

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

logger: logging.Logger = logging.getLogger(__name__)

logger.debug("Initializing Event Loop...")
loop = asyncio.get_event_loop()

logger.info("Initializing Config...")
config: Config = Config()
logger.info("Config initialized.")


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
    intents=intents,
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


@bot.event
async def on_application_command_error(ctx: ApplicationContext, exception: Exception) -> None:
    """|coro|
    The default command error handler provided by the bot.
    By default this prints to :data:`sys.stderr` however it could be
    overridden to have a different implementation.
    This only fires if you do not specify any listeners for command error.
    """
    EXCEPTION_LOG_CHANNEL_ID = os.environ.get("EXCEPTION_LOG_CHANNEL")
    log_channel: Messageable | None = bot.get_channel(int(EXCEPTION_LOG_CHANNEL_ID))

    if isinstance(exception, CheckFailure):
        await ctx.interaction.response.send_message(
            chat_formatting.error(
                "You do not have permission to use this command. Sucks to be you."
            ),
            ephemeral=True,
        )
        if log_channel is not None:
            await log_channel.send(
                f"{ctx.author.mention} tried to use `/{ctx.command.qualified_name}` but failed a check."
            )
        return

    traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)

    await ctx.respond(
        chat_formatting.error(f"An error occurred: {chat_formatting.inline(str(exception))}"),
        ephemeral=True,
    )

    if log_channel is not None:
        await log_channel.send(
            f"Exception in command `/{ctx.command.qualified_name}`: {chat_formatting.inline(exception)}",
            file=chat_formatting.text_to_file(
                "".join(
                    traceback.format_exception(type(exception), exception, exception.__traceback__)
                ),
                "traceback.txt",
            ),
        )


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
