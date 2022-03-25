import logging
from typing import TYPE_CHECKING, NoReturn

from discord import Bot, Cog as Cog_
from discord.utils import utcnow

from trainerdex_discord_bot.exceptions import CogHealthcheckException

if TYPE_CHECKING:
    from trainerdex.client import Client

    from trainerdex_discord_bot.config import Config
    from trainerdex_discord_bot.datatypes import CogMeta, Common

logger: logging.Logger = logging.getLogger(__name__)


class Cog(Cog_):
    def __init__(self, common: "Common") -> None:
        logger.info("Initializing %s...", self.__class__.__name__)
        self._common: Common = common
        self.bot: Bot = common.bot
        self.config: Config = common.config
        self.client: Client = common.client
        self.bot.loop.create_task(self.__post_init__())

    async def __post_init__(self) -> None:
        try:
            await self._healthcheck()
        except CogHealthcheckException as e:
            logger.exception(
                "Healthcheck failed on %s, unloading cog.", self.__class__.__name__, exc_info=e
            )
            self.bot.remove_cog(self.__class__.__name__)
            return

        logger.info("%s successfully initialized.", self.__class__.__name__)

        _meta: CogMeta = await self.config.get_cog_meta(self)
        _meta.last_loaded = utcnow()
        await self.config.set_cog_meta(_meta)

    async def _healthcheck(self) -> NoReturn | None:
        ...
