"""
Official TrainerDex API Wrapper
-------------------------------

A basic wrapper for the TrainerDex API.

:copyright: (c) 2020 TurnrDev
:licence: GNU-GPL3, see LICENSE for more details

"""

__title__ = "trainerdex"
__author__ = "JayTurnr"
__licence__ = "GNU-GPL"
__copyright__ = "Copyright 2020 TurnrDev"
__version__ = "4.0.0a"

from .client import Client
from .http import Route, HTTPClient
from .leaderboard import Leaderboard, GuildLeaderboard
from .faction import Faction
from .trainer import Trainer
from .update import Update
from .user import User
