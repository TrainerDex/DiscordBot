import asyncio
import datetime
import logging
import os

from discord import ApplicationContext, Bot, CheckFailure, Game, Intents
from trainerdex.client import Client

from trainerdex_discord_bot import __version__
from trainerdex_discord_bot.cogs.interface import Cog
from trainerdex_discord_bot.config import Config
from trainerdex_discord_bot.constants import DEBUG, DEBUG_GUILDS, TRAINERDEX_API_TOKEN
from trainerdex_discord_bot.datatypes import Common
from trainerdex_discord_bot.loggers import DiscordLogger, getLogger
from trainerdex_discord_bot.utils import chat_formatting

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

private_logger: logging.Logger = logging.getLogger(__name__)


async def main(loop: asyncio.AbstractEventLoop) -> None:
    private_logger.info("Initializing Config...")
    config: Config = Config()
    private_logger.info("Config initialized.")

    async def set_presence_to_version(bot: Bot) -> None:
        await bot.wait_until_ready()
        private_logger.info("Setting presence to version %s...", __version__)
        await bot.change_presence(activity=Game(name=__version__))

    private_logger.info("Initializing Pycord...")
    intents = Intents.default()
    intents.members = True
    intents.message_content = True

    bot: Bot = Bot(
        debug_guilds=DEBUG_GUILDS if DEBUG else None,
        description="TrainerDex, a Discord bot for Pokémon Go.",
        intents=intents,
        loop=loop,
    )
    private_logger.info("Pycord initialized.")
    logger: DiscordLogger = getLogger(bot, __name__)

    @bot.event
    async def on_ready() -> None:
        private_logger.info(
            "Bot ready! Logged in as %(user)s (%(user_id)s). %(num_guilds)s guilds.",
            {
                "user": bot.user,
                "user_id": bot.user.id,
                "num_guilds": len(bot.guilds),
            },
        )
        await set_presence_to_version(bot)
        app_info = await bot.application_info()
        private_logger.info(
            "Bot %(name)s hosted by %(owner)s (%(owner_id)s), created by @TurnrDev.",
            {
                "name": app_info.name,
                "owner": (app_info.team and f"{app_info.team.name} Team") or app_info.owner,
                "owner_id": (app_info.team and app_info.team.id) or app_info.owner.id,
            },
        )
        private_logger.info("Public: %(public)s", {"public": app_info.bot_public})
        logger.info("Bot loaded at {time}.".format(time=datetime.datetime.utcnow().isoformat()))

    @bot.event
    async def on_application_command_error(ctx: ApplicationContext, exception: Exception) -> None:
        """|coro|
        The default command error handler provided by the bot.
        By default this prints to :data:`sys.stderr` however it could be
        overridden to have a different implementation.
        This only fires if you do not specify any listeners for command error.
        """

        if isinstance(exception, CheckFailure):
            await ctx.interaction.response.send_message(
                chat_formatting.error(
                    "You do not have permission to use this command. Sucks to be you."
                ),
                ephemeral=True,
            )
            logger.warning(
                f"{ctx.author.mention} tried to use `/{ctx.command.qualified_name}` but failed a check."
            )
            return

        logger.exception(
            f"Exception in command `/{ctx.command.qualified_name}`: {chat_formatting.inline(exception)}",
            exception,
        )

        await ctx.respond(
            chat_formatting.error(f"An error occurred: {chat_formatting.inline(str(exception))}"),
            ephemeral=True,
        )

    private_logger.info("Initializing TrainerDex API Client...")
    client: Client = Client(token=TRAINERDEX_API_TOKEN, loop=loop)
    private_logger.info("Pycord initialized.")

    # Construct Common dataclass
    common: Common = Common(
        bot=bot,
        config=config,
        client=client,
    )

    private_logger.info("Loading cogs...")
    for cog in Cog.__subclasses__():
        bot.add_cog(cog(common))

    try:
        private_logger.info("Running bot...")
        await bot.start(os.environ["DISCORD_TOKEN"])
    except KeyboardInterrupt:
        await bot.close()
    except Exception as e:
        private_logger.exception(e)
        await bot.close()


if __name__ == "__main__":

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(loop))
    finally:
        loop.close()
