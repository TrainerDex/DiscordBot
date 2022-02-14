from __future__ import annotations

import os
from distutils.util import strtobool
from discord import PartialEmoji
from enum import Enum
from lenum import LabeledEnum
from typing import Optional


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
    GYMBADGES_GOLD = PartialEmoji(name="gym_badge", id=743853262469333042)
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


class Stats(LabeledEnum):
    # Top 4 stats, we definitely want these
    TOTAL_XP = "total_xp", "Total XP"
    POKESTOPS_VISITED = "badge_pokestops_visited", "Backpacker"
    CAPTURE_TOTAL = "badge_capture_total", "Collector"
    TRAVEL_KM = "badge_travel_km", "Jogger"

    # Gold Gym badges, we want this
    GYMBADGES_GOLD = "gymbadges_gold", "Gold Gym Badges"
    UNIQUE_POKESTOPS = "badge_unique_pokestops", "Sightseer"

    EVOLVED_TOTAL = "badge_evolved_total", "Scientist"
    HATCHED_TOTAL = "badge_hatched_total", "Breeder"
    BIG_MAGIKARP = "badge_big_magikarp", "Fisher"
    BATTLE_ATTACK_WON = "badge_battle_attack_won", "Battle Girl"
    BATTLE_TRAINING_WON = "badge_battle_training_won", "Ace Trainer"
    SMALL_RATTATA = "badge_small_rattata", "Youngster"
    PIKACHU = "badge_pikachu", "Pikachu Fan"
    UNOWN = "badge_unown", "Unown"
    RAID_BATTLE_WON = "badge_raid_battle_won", "Champion"
    LEGENDARY_BATTLE_WON = "badge_legendary_battle_won", "Battle Legend"
    BERRIES_FED = "badge_berries_fed", "Berry Master"
    HOURS_DEFENDED = "badge_hours_defended", "Gym Leader"
    CHALLENGE_QUESTS = "badge_challenge_quests", "Pokémon Ranger"
    MAX_LEVEL_FRIENDS = "badge_max_level_friends", "Idol"
    TRADING = "badge_trading", "Gentleman"
    TRADING_DISTANCE = "badge_trading_distance", "Pilot"
    GREAT_LEAGUE = "badge_great_league", "Great League Veteran"
    ULTRA_LEAGUE = "badge_ultra_league", "Ultra League Veteran"
    MASTER_LEAGUE = "badge_master_league", "Master League Veteran"
    PHOTOBOMB = "badge_photobomb", "Cameraman"
    POKEMON_PURIFIED = "badge_pokemon_purified", "Purifier"
    ROCKET_GRUNTS_DEFEATED = "badge_rocket_grunts_defeated", "Hero"
    ROCKET_GIOVANNI_DEFEATED = "badge_rocket_giovanni_defeated", "Ultra Hero"
    BUDDY_BEST = "badge_buddy_best", "Best Buddy"
    SEVEN_DAY_STREAKS = "badge_7_day_streaks", "Triathlete"
    UNIQUE_RAID_BOSSES_DEFEATED = "badge_unique_raid_bosses_defeated", "Rising Star"
    RAIDS_WITH_FRIENDS = "badge_raids_with_friends", "Rising Star Duo"
    POKEMON_CAUGHT_AT_YOUR_LURES = "badge_pokemon_caught_at_your_lures", "Picnicker"
    WAYFARER = "badge_wayfarer", "Wayfarer"
    TOTAL_MEGA_EVOS = "badge_total_mega_evos", "Successor"
    UNIQUE_MEGA_EVOS = "badge_unique_mega_evos", "Mega Evolution Guru"
