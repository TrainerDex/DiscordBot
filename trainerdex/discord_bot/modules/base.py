import logging
from typing import TYPE_CHECKING, NoReturn

import pymongo.errors
from discord import Bot, Cog
from discord.utils import utcnow

from trainerdex.api.client import TokenClient
from trainerdex.discord_bot.constants import TRAINERDEX_API_TOKEN
from trainerdex.discord_bot.exceptions import ModuleHealthCheckException
from trainerdex.discord_bot.loggers import getLogger

if TYPE_CHECKING:
    from trainerdex.discord_bot.config import Config
    from trainerdex.discord_bot.datatypes import Common, ModuleMeta


class Module(Cog):
    def __init__(self, common: "Common") -> None:
        self.private_logger: logging.Logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__qualname__}"
        )
        self.private_logger.info("Initializing module...")
        self._common: Common = common
        self.bot: Bot = common.bot
        self.config: Config = common.config
        self.bot.loop.create_task(self.__post_init__())
        self.logger = getLogger(self.bot, f"{self.__class__.__module__}.{self.__class__.__qualname__}")

    @classmethod
    @property
    def METADATA_ID(cls) -> str:
        raise NotImplementedError

    def client(self) -> TokenClient:
        return TokenClient(loop=self.bot.loop).authenticate(token=TRAINERDEX_API_TOKEN)

    async def __post_init__(self) -> None:
        try:
            await self._healthcheck()
        except ModuleHealthCheckException:
            self.private_logger.exception("Healthcheck failed, unloading module.")
            self.bot.remove_cog(self.__class__.__name__)
            return

        self.private_logger.info("Module successfully initialized.")

        try:
            _meta: ModuleMeta = await self.config.get_module_metadata(self)
            _meta.last_loaded = utcnow()
            await self.config.set_module_metadata(_meta)
        except pymongo.errors.PyMongoError:
            self.private_logger.exception("Failed to update module metadata.")

    async def _healthcheck(self) -> NoReturn | None:
        ...
