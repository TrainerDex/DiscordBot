from discord import Message
from discord.ext.commands import Bot
from trainerdex.discord.config import Config
from trainerdex.discord.constants import DEBUG, DEBUG_GUILDS, DEFAULT_PREFIX, DISCORD_OWNER_IDS
from trainerdex.discord.core import TrainerDex

bot = Bot()


def get_prefix(bot: Bot, message: Message) -> str:
    config = Config()
    if message.guild:
        return config.get_guild(message.guild).prefix
    return DEFAULT_PREFIX


bot.run(
    allowed_mentions=True,
    debug_guilds=DEBUG_GUILDS if DEBUG else None,
    description="TrainerDex, a Discord bot for Pokemon Go.",
    case_insensitive=True,
    command_prefix=get_prefix,
    strip_after_prefix=True,  # Set true as iPhone is a bitch.
    owner_ids=DISCORD_OWNER_IDS,
)
bot.add_cog(TrainerDex(bot))
