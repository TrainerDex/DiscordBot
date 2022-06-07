from __future__ import annotations

import os
from distutils.util import strtobool
from enum import Enum

from discord import PartialEmoji
from lenum import LabeledEnum

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

    LEGENDARY_BATTLE_WON = "badge_legendary_battle_won", "Battle Legend"  # 20
    RAID_BATTLE_WON = "badge_raid_battle_won", "Champion"  # 18
    HOURS_DEFENDED = "badge_hours_defended", "Gym Leader"  # 18
    CHALLENGE_QUESTS = "badge_challenge_quests", "Pokémon Ranger"  # 17
    EVOLVED_TOTAL = "badge_evolved_total", "Scientist"  # 16
    TRADING_DISTANCE = "badge_trading_distance", "Pilot"  # 14
    HATCHED_TOTAL = "badge_hatched_total", "Breeder"  # 12
    ROCKET_GRUNTS_DEFEATED = "badge_rocket_grunts_defeated", "Hero"  # 10
    TRADING = "badge_trading", "Gentleman"  # 9
    BATTLE_ATTACK_WON = "badge_battle_attack_won", "Battle Girl"  # 8
    WAYFARER = "badge_wayfarer", "Wayfarer"  # 6
    BERRIES_FED = "badge_berries_fed", "Berry Master"  # 4
    BUDDY_BEST = "badge_buddy_best", "Best Buddy"  # -2
    GREAT_LEAGUE = "badge_great_league", "Great League Veteran"  # -3
    ULTRA_LEAGUE = "badge_ultra_league", "Ultra League Veteran"  # -3
    TOTAL_MEGA_EVOS = "badge_total_mega_evos", "Successor"  # -3
    SEVEN_DAY_STREAKS = "badge_7_day_streaks", "Triathlete"  # -4
    MASTER_LEAGUE = "badge_master_league", "Master League Veteran"  # -4
    ROCKET_GIOVANNI_DEFEATED = "badge_rocket_giovanni_defeated", "Ultra Hero"  # -4
    POKEMON_CAUGHT_AT_YOUR_LURES = "badge_pokemon_caught_at_your_lures", "Picnicker"  # -4
    RAIDS_WITH_FRIENDS = "badge_raids_with_friends", "Rising Star Duo"  # -6
    UNIQUE_MEGA_EVOS = "badge_unique_mega_evos", "Mega Evolution Guru"  # -7
    BIG_MAGIKARP = "badge_big_magikarp", "Fisher"  # -8
    PIKACHU = "badge_pikachu", "Pikachu Fan"  # -12
    BATTLE_TRAINING_WON = "badge_battle_training_won", "Ace Trainer"  # -13
    MAX_LEVEL_FRIENDS = "badge_max_level_friends", "Idol"  # -13
    UNOWN = "badge_unown", "Unown"  # -14
    UNIQUE_RAID_BOSSES_DEFEATED = "badge_unique_raid_bosses_defeated", "Rising Star"  # -13
    PHOTOBOMB = "badge_photobomb", "Cameraman"  # -14
    POKEMON_PURIFIED = "badge_pokemon_purified", "Purifier"  # -14
    SMALL_RATTATA = "badge_small_rattata", "Youngster"  # -16


STAT_MAP = {
    "travel_km": "badge_travel_km",
    "pokedex_entries": "bagde_pokedex_entries",
    "capture_total": "badge_capture_total",
    "evolved_total": "badge_evolved_total",
    "hatched_total": "badge_hatched_total",
    "pokestops_visited": "badge_pokestops_visited",
    "unique_pokestops": "badge_unique_pokestops",
    "big_magikarp": "badge_big_magikarp",
    "battle_attack_won": "badge_battle_attack_won",
    "battle_training_won": "badge_battle_training_won",
    "small_rattata": "badge_small_rattata",
    "pikachu": "badge_pikachu",
    "unown": "badge_unown",
    "pokedex_entries_gen2": "badge_pokedex_entries_gen2",
    "raid_battle_won": "badge_raid_battle_won",
    "legendary_battle_won": "badge_legendary_battle_won",
    "berries_fed": "badge_berries_fed",
    "hours_defended": "badge_hours_defended",
    "pokedex_entries_gen3": "badge_pokedex_entries_gen3",
    "challenge_quests": "badge_challenge_quests",
    "max_level_friends": "badge_max_level_friends",
    "trading": "badge_trading",
    "trading_distance": "badge_trading_distance",
    "pokedex_entries_gen4": "badge_pokedex_entries_gen4",
    "great_league": "badge_great_league",
    "ultra_league": "badge_ultra_league",
    "master_league": "badge_master_league",
    "photobomb": "badge_photobomb",
    "pokedex_entries_gen5": "badge_pokedex_entries_gen5",
    "pokemon_purified": "badge_pokemon_purified",
    "rocket_grunts_defeated": "badge_rocket_grunts_defeated",
    "rocket_giovanni_defeated": "badge_rocket_giovanni_defeated",
    "buddy_best": "badge_buddy_best",
    "pokedex_entries_gen6": "badge_pokedex_entries_gen6",
    "pokedex_entries_gen7": "badge_pokedex_entries_gen7",
    "pokedex_entries_gen8": "badge_pokedex_entries_gen8",
    "seven_day_streaks": "badge_seven_day_streaks",
    "unique_raid_bosses_defeated": "badge_unique_raid_bosses_defeated",
    "raids_with_friends": "badge_raids_with_friends",
    "pokemon_caught_at_your_lures": "badge_pokemon_caught_at_your_lures",
    "wayfarer": "badge_wayfarer",
    "total_mega_evos": "badge_total_mega_evos",
    "unique_mega_evos": "badge_unique_mega_evos",
    "mvt": "badge_mvt",
    "mini_collection": "badge_mini_collection",
    "battle_hub_stats_wins": "badge_battle_hub_stats_wins",
    "type_normal": "badge_type_normal",
    "type_fighting": "badge_type_fighting",
    "type_flying": "badge_type_flying",
    "type_poison": "badge_type_poison",
    "type_ground": "badge_type_ground",
    "type_rock": "badge_type_rock",
    "type_bug": "badge_type_bug",
    "type_ghost": "badge_type_ghost",
    "type_steel": "badge_type_steel",
    "type_fire": "badge_type_fire",
    "type_water": "badge_type_water",
    "type_grass": "badge_type_grass",
    "type_electric": "badge_type_electric",
    "type_psychic": "badge_type_psychic",
    "type_ice": "badge_type_ice",
    "type_dragon": "badge_type_dragon",
    "type_dark": "badge_type_dark",
    "type_fairy": "badge_type_fairy",
    "gym_gold": "gymbadges_gold",
}
