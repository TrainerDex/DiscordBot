import logging
from typing import TYPE_CHECKING, NoReturn

from discord import Bot
from discord import Cog as Cog_
from discord.utils import utcnow

from trainerdex_discord_bot.exceptions import CogHealthcheckException
from trainerdex_discord_bot.loggers import getLogger

if TYPE_CHECKING:
    from trainerdex.client import Client

    from trainerdex_discord_bot.config import Config
    from trainerdex_discord_bot.datatypes import CogMeta, Common


class Cog(Cog_):
    def __init__(self, common: "Common") -> None:
        self.private_logger: logging.Logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__qualname__}"
        )
        self.private_logger.info("Initializing cog...")
        self._common: Common = common
        self.bot: Bot = common.bot
        self.config: Config = common.config
        self.client: Client = common.client
        self.bot.loop.create_task(self.__post_init__())
        self.logger = getLogger(
            self.bot, f"{self.__class__.__module__}.{self.__class__.__qualname__}"
        )

    async def __post_init__(self) -> None:
        try:
            await self._healthcheck()
        except CogHealthcheckException:
            self.private_logger.exception("Healthcheck failed, unloading cog.")
            self.bot.remove_cog(self.__class__.__name__)
            return

        self.private_logger.info("Cog successfully initialized.")

        _meta: CogMeta = await self.config.get_cog_meta(self)
        _meta.last_loaded = utcnow()
        await self.config.set_cog_meta(_meta)

    async def _healthcheck(self) -> NoReturn | None:
        ...
