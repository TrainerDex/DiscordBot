from __future__ import annotations

import os
from distutils.util import strtobool
from enum import Enum

from discord import PartialEmoji

SOCIAL_TWITTER: str = "@TrainerDexApp"
SOCIAL_INSTAGRAM: str = "@TrainerDexApp"
SOCIAL_REDDIT: str = "https://reddit.com/r/TrainerDex"

ADMIN_GUILD_ID: int = int(os.environ.get("ADMIN_GUILD", "364313717720219651"))
ADMIN_LOG_CHANNEL_ID: int = int(os.environ.get("ADMIN_LOG_CHANNEL", "393177706029776898"))

DEBUG: bool = strtobool(str(os.environ.get("DEBUG", False)).lower())
DEBUG_GUILDS: list[int] = [int(x) for x in os.environ.get("DEBUG_GUILDS", "").split(",")] or [
    ADMIN_GUILD_ID
]

WEBSITE_DOMAIN: str = "https://trainerdex.app"

TRAINERDEX_API_TOKEN: str = os.environ.get("TRAINERDEX_API_TOKEN")


class CustomEmoji(Enum):
    DATE = PartialEmoji(name="date", id=743874800547791023)
    GYM = PartialEmoji(name="global", id=743874196639056096)
    TEAMLESS = PartialEmoji(name="teamless", id=743873748029145209)
    ADD_FRIEND = PartialEmoji(name="add_friend", id=743853499170947234)
    PROFILE = PartialEmoji(name="profile", id=43853381919178824)
    GYM_BADGE = PartialEmoji(name="gym_badge", id=743853262469333042)
    GYMBADGES_GOLD = PartialEmoji(name="gym_badge", id=743853262469333042)
    GYM_GOLD = PartialEmoji(name="gym_badge", id=743853262469333042)
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
    # Top 4 stats, we definitely want these
    TOTAL_XP = "total_xp", "Total XP"
    POKESTOPS_VISITED = "pokestops_visited", "Backpacker"
    CAPTURE_TOTAL = "capture_total", "Collector"
    TRAVEL_KM = "travel_km", "Jogger"

    # Gold Gym badges, we want this
    GYM_GOLD = "gym_gold", "Gold Gym Badges"
    UNIQUE_POKESTOPS = "unique_pokestops", "Sightseer"

    LEGENDARY_BATTLE_WON = "legendary_battle_won", "Battle Legend"  # 20
    RAID_BATTLE_WON = "raid_battle_won", "Champion"  # 18
    HOURS_DEFENDED = "hours_defended", "Gym Leader"  # 18
    CHALLENGE_QUESTS = "challenge_quests", "Pokémon Ranger"  # 17
    EVOLVED_TOTAL = "evolved_total", "Scientist"  # 16
    TRADING_DISTANCE = "trading_distance", "Pilot"  # 14
    HATCHED_TOTAL = "hatched_total", "Breeder"  # 12
    ROCKET_GRUNTS_DEFEATED = "rocket_grunts_defeated", "Hero"  # 10
    TRADING = "trading", "Gentleman"  # 9
    BATTLE_ATTACK_WON = "battle_attack_won", "Battle Girl"  # 8
    WAYFARER = "wayfarer", "Wayfarer"  # 6
    BERRIES_FED = "berries_fed", "Berry Master"  # 4
    BUDDY_BEST = "buddy_best", "Best Buddy"  # -2
    GREAT_LEAGUE = "great_league", "Great League Veteran"  # -3
    ULTRA_LEAGUE = "ultra_league", "Ultra League Veteran"  # -3
    TOTAL_MEGA_EVOS = "total_mega_evos", "Successor"  # -3
    SEVEN_DAY_STREAKS = "seven_day_streaks", "Triathlete"  # -4
    MASTER_LEAGUE = "master_league", "Master League Veteran"  # -4
    ROCKET_GIOVANNI_DEFEATED = "rocket_giovanni_defeated", "Ultra Hero"  # -4
    POKEMON_CAUGHT_AT_YOUR_LURES = "pokemon_caught_at_your_lures", "Picnicker"  # -4
    RAIDS_WITH_FRIENDS = "raids_with_friends", "Rising Star Duo"  # -6
    UNIQUE_MEGA_EVOS = "unique_mega_evos", "Mega Evolution Guru"  # -7
    BIG_MAGIKARP = "big_magikarp", "Fisher"  # -8
    PIKACHU = "pikachu", "Pikachu Fan"  # -12
    BATTLE_TRAINING_WON = "battle_training_won", "Ace Trainer"  # -13
    MAX_LEVEL_FRIENDS = "max_level_friends", "Idol"  # -13
    UNOWN = "unown", "Unown"  # -14
    UNIQUE_RAID_BOSSES_DEFEATED = "unique_raid_bosses_defeated", "Rising Star"  # -13
    PHOTOBOMB = "photobomb", "Cameraman"  # -14
    POKEMON_PURIFIED = "pokemon_purified", "Purifier"  # -14
    SMALL_RATTATA = "small_rattata", "Youngster"  # -16


STAT_MAP = {
    "pokedex_entries": "pokedex_gen1",
    "pokedex_entries_gen2": "pokedex_gen2",
    "pokedex_entries_gen3": "pokedex_gen3",
    "pokedex_entries_gen4": "pokedex_gen4",
    "pokedex_entries_gen5": "pokedex_gen5",
    "pokedex_entries_gen6": "pokedex_gen6",
    "pokedex_entries_gen7": "pokedex_gen7",
    "pokedex_entries_gen8": "pokedex_gen8",
    "gym_gold": "gymbadges_gold",
}
