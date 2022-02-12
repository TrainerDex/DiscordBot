import os


SOCIAL_TWITTER: str = "@TrainerDexApp"
SOCIAL_INSTAGRAM: str = "@TrainerDexApp"
SOCIAL_REDDIT: str = "https://reddit.com/r/TrainerDex"

DISCORD_ADMIN_USER_IDS: list[int] = [
    int(x) for x in os.environ.get("DISCORD_ADMIN_USER_IDS", "").split(",")
]
"""A comma-separated (and parsed) list of user IDs that are considered to be Admins over the bot. Type: int"""
DISCORD_SUPERUSER_USER_ID: int = int(os.environ.get("DISCORD_SUPERUSER_USER_ID"))
"""This should be set the the bot owner's user ID. Type: int"""

WEBSITE_DOMAIN: str = "https://trainerdex.app"
