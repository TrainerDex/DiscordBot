from abc import ABC

from discord.ext.commands import Bot
from trainerdex.client import Client
from trainerdex_discord_bot.config import Config


class MixinMeta(ABC):
    def __init__(self, *_args):
        self.bot: Bot
        self.config: Config
        self.client: Client
