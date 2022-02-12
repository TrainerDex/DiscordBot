from __future__ import annotations

import os
from distutils.util import strtobool
from enum import Enum
from typing import Optional


SOCIAL_TWITTER: str = "@TrainerDexApp"
SOCIAL_INSTAGRAM: str = "@TrainerDexApp"
SOCIAL_REDDIT: str = "https://reddit.com/r/TrainerDex"

DEBUG: bool = strtobool(str(os.environ.get("DEBUG", False)).lower())
DEBUG_GUILDS: Optional[list[int]] = [int(x) for x in os.environ.get("DEBUG_GUILDS", "").split(",")]

DISCORD_OWNER_IDS: Optional[set[int]] = set(
    [int(x) for x in os.environ.get("DISCORD_OWNER_IDS", "").split(",")]
)
"""A comma-separated (and parsed) list of user IDs that are considered to be Admins over the bot. Type: int"""

WEBSITE_DOMAIN: str = "https://trainerdex.app"

POGOOCR_TOKEN_PATH: str = os.environ.get("POGOOCR_TOKEN_PATH")
TRAINERDEX_API_TOKEN: str = os.environ.get("TRAINERDEX_API_TOKEN")

DEFAULT_PREFIX: str = os.environ.get("DEFAULT_PREFIX", ".")


class CUSTOM_EMOJI(Enum):
    TEAMLESS = 743873748029145209
    MYSTIC = 430113444558274560
    VALOR = 430113457149575168
    INSTINCT = 430113431333371924
    TRAVEL_KM = 743122298126467144
    BADGE_TRAVEL_KM = 743122298126467144
    CAPTURE_TOTAL = 743122649529450566
    BADGE_CAPTURE_TOTAL = 743122649529450566
    POKESTOPS_VISITED = 743122864303243355
    BADGE_POKESTOPS_VISITED = 743122864303243355
    TOTAL_XP = 743121748630831165
    GIFT = 743120044615270616
    ADD_FRIEND = 743853499170947234
    PREVIOUS = 729769958652772505
    NEXT = 729770058099982347
    LOADING = 471298325904359434
    GLOBAL = 743853198217052281
    GYM = 743874196639056096
    GYM_BADGE = 743853262469333042
    GYMBADGES_GOLD = 743853262469333042
    PROFILE = 43853381919178824
    DATE = 743874800547791023
