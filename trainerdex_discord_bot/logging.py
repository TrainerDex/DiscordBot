import logging
import traceback
from enum import Enum
from typing import Callable

from discord import Bot, Forbidden, HTTPException, InvalidArgument, TextChannel
from promise import promisify

from trainerdex_discord_bot.constants import ADMIN_LOG_CHANNEL_ID
from trainerdex_discord_bot.utils.chat_formatting import (
    error,
    info,
    text_to_file,
    warning,
)


class LoggerLevel(int, Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


message_formatters: dict[LoggerLevel, Callable[[str], str]] = {
    LoggerLevel.DEBUG: info,
    LoggerLevel.INFO: info,
    LoggerLevel.WARNING: warning,
    LoggerLevel.ERROR: error,
    LoggerLevel.CRITICAL: error,
}


class DiscordLogger:
    def __init__(self, bot: Bot, name: str, **kwargs):
        self.bot = bot
        self.name = name
        self.level = kwargs.get("level") or LoggerLevel.INFO
        self.channel_id = kwargs.get("channel_id") or ADMIN_LOG_CHANNEL_ID
        self._channel = None
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.level.value)

    @property
    def channel(self) -> TextChannel | None:
        if self._channel is None:
            self._channel = self.bot.get_channel(int(self.channel_id))

        if isinstance(self._channel, TextChannel):
            return self._channel

    @promisify
    async def _send_message(
        self, message: str, level: LoggerLevel, *, exception: Exception = None
    ) -> None:
        formatted_message = message_formatters[level](message)

        if exception:
            file = text_to_file(
                "".join(
                    traceback.format_exception(type(exception), exception, exception.__traceback__)
                ),
                "traceback.txt",
            )
        else:
            file = None

        message = None
        attempts = 0
        while message is None and attempts < 3:
            attempts += 1
            try:
                message = await self.channel.send(formatted_message, file=file)
            except (HTTPException, Forbidden, InvalidArgument, AttributeError):
                self.logger.exception("Failed to send log message to Discord.")

    @promisify
    async def debug(self, msg: str, *args, **kwargs) -> None:
        self.logger.debug(msg, *args, **kwargs)
        if self.level <= LoggerLevel.DEBUG:
            await self._send_message(msg, LoggerLevel.DEBUG)

    @promisify
    async def info(self, msg: str, *args, **kwargs) -> None:
        self.logger.info(msg, *args, **kwargs)
        if self.level <= LoggerLevel.INFO:
            await self._send_message(msg, LoggerLevel.INFO)

    @promisify
    async def warning(self, msg: str, *args, **kwargs) -> None:
        self.logger.warning(msg, *args, **kwargs)
        if self.level <= LoggerLevel.WARNING:
            await self._send_message(msg, LoggerLevel.WARNING)

    @promisify
    async def error(self, msg: str, *args, **kwargs) -> None:
        self.logger.error(msg, *args, **kwargs)
        if self.level <= LoggerLevel.ERROR:
            await self._send_message(msg, LoggerLevel.ERROR)

    @promisify
    async def exception(self, msg: str, exception: Exception, *args, **kwargs) -> None:
        self.logger.exception(msg, *args, **kwargs)
        if self.level <= LoggerLevel.ERROR:
            await self._send_message(msg, LoggerLevel.ERROR, exception=exception)

    @promisify
    async def critical(self, msg: str, *args, **kwargs) -> None:
        self.logger.critical(msg, *args, **kwargs)
        if self.level <= LoggerLevel.CRITICAL:
            await self._send_message(msg, LoggerLevel.CRITICAL)


def getLogger(bot, name=None, level=None) -> DiscordLogger:
    """
    Return a logger with the specified name, creating it if necessary.

    If no name is specified, return the root logger.
    """
    if not name or isinstance(name, str) and name == "root":
        return DiscordLogger(bot, "root", level=level)
    return DiscordLogger(bot, name, level=level)
