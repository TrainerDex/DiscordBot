from abc import ABC
from typing import Dict

from redbot.core import Config
from redbot.core.bot import Red
from trainerdex import Client


class MixinMeta(ABC):
    """
    Base class for well behaved type hint detection with composite class.

    Basically, to keep developers sane when not all attributes are defined in each mixin.
    """

    def __init__(self, *_args):
        self.bot: Red
        self.config: Config
        self.client: Client
        self.emoji: Dict
