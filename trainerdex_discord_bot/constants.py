from __future__ import annotations

import os
from distutils.util import strtobool
from discord import PartialEmoji
from enum import Enum
from typing import Mapping, Optional


SOCIAL_TWITTER: str = "@TrainerDexApp"
SOCIAL_INSTAGRAM: str = "@TrainerDexApp"
SOCIAL_REDDIT: str = "https://reddit.com/r/TrainerDex"

DEBUG: bool = strtobool(str(os.environ.get("DEBUG", False)).lower())
DEBUG_GUILDS: Optional[list[int]] = [int(x) for x in os.environ.get("DEBUG_GUILDS", "").split(",")]

DISCORD_OWNER_IDS: Optional[set[int]] = set(
    [int(x) for x in os.environ.get("DISCORD_OWNER_IDS", "").split(",")]
)

WEBSITE_DOMAIN: str = "https://trainerdex.app"

POGOOCR_TOKEN_PATH: str = os.environ.get("POGOOCR_TOKEN_PATH")
TRAINERDEX_API_TOKEN: str = os.environ.get("TRAINERDEX_API_TOKEN")

DEFAULT_PREFIX: str = os.environ.get("DEFAULT_PREFIX", ".")


class CustomEmoji(Enum):
    DATE = PartialEmoji(name="date", id=743874800547791023)
    GYM = PartialEmoji(name="global", id=743874196639056096)
    TEAMLESS = PartialEmoji(name="teamless", id=743873748029145209)
    ADD_FRIEND = PartialEmoji(name="add_friend", id=743853499170947234)
    PROFILE = PartialEmoji(name="profile", id=43853381919178824)
    GYM_BADGE = PartialEmoji(name="gym_badge", id=743853262469333042)
    GLOBAL = PartialEmoji(name="global", id=743853198217052281)
    POKESTOPS_VISITED = PartialEmoji(name="pokestops_visited", id=743122864303243355)
    CAPTURE_TOTAL = PartialEmoji(name="capture_total", id=743122649529450566)
    TRAVEL_KM = PartialEmoji(name="travel_km", id=743122298126467144)
    BADGE_POKESTOPS_VISITED = PartialEmoji(name="pokestops_visited", id=743122864303243355)
    BADGE_CAPTURE_TOTAL = PartialEmoji(name="capture_total", id=743122649529450566)
    BADGE_TRAVEL_KM = PartialEmoji(name="travel_km", id=743122298126467144)
    TOTAL_XP = PartialEmoji(name="total_xp", id=743121748630831165)
    GIFT = PartialEmoji(name="gift", id=743120044615270616)
    PREVIOUS = PartialEmoji(name="arrow_left", id=729769958652772505)
    NEXT = PartialEmoji(name="arrow_right", id=729770058099982347)
    MYSTIC = PartialEmoji(name="mystic", id=430113444558274560)
    VALOR = PartialEmoji(name="valor", id=430113457149575168)
    INSTINCT = PartialEmoji(name="instinct", id=430113431333371924)
    LOADING = PartialEmoji(name="loading", id=471298325904359434, animated=True)
    TRAINERDEX = PartialEmoji(name="TrainerDex", id=734168947372326953)


class Stats(Enum):
    TOTAL_XP = "total_xp"
    TRAVEL_KM = "badge_travel_km"


STAT_VERBOSE_MAPPING: Mapping[str, str] = {
    Stats.TOTAL_XP.value: "Total XP",
    Stats.TRAVEL_KM.value: "Jogger",
}
