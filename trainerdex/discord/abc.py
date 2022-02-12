from abc import ABC
from typing import Dict, Union
from discord import Bot
from discord.emoji import Emoji
from trainerdex.client import Client


class MixinMeta(ABC):
    def __init__(self, *_args):
        self.bot: Bot
        self.config: None  # TBD
        self.client: Client
        self.emoji: Dict[str, Union[str, Emoji]]
