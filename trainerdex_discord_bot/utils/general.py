from discord import ApplicationContext
from discord.abc import User
from trainerdex.trainer import Trainer

from trainerdex_discord_bot.constants import SOCIAL_TWITTER
from trainerdex_discord_bot.utils import chat_formatting


def append_twitter(text: str) -> str:
    return f"{text}\n\nIf that doesn't look right, please contact us on Twitter. {SOCIAL_TWITTER}"


def introduction_notes(
    ctx: ApplicationContext, member: User, trainer: Trainer, additional_message: str
) -> str:
    BASE_NOTE = """**You're getting this message because you have been added to the TrainerDex database.**

This would likely be in response to you joining `{server.name}` and posting your screenshots for a mod to approve.

TrainerDex is a Pokémon Go trainer database and leaderboard. View our privacy policy here:
<{privacy_policy_url}>

If you have any questions, please contact us on Twitter (<{twitter_handle}>), ask the mod who approved you ({mod.mention})."""
    BASE_NOTE = BASE_NOTE.format(
        server=ctx.guild,
        mod=ctx.author,
        privacy_policy_url="https://trainerdex.app/legal/privacy/",
        twitter_handle="https://twitter.com/TrainerDexApp",
    )

    if additional_message:
        ADDITIONAL_NOTE = (
            "Additionally, you have a message from `{server.name}`:\n{note}"
        ).format(server=ctx.guild, note=chat_formatting.quote(additional_message))
        return (BASE_NOTE, ADDITIONAL_NOTE)
    else:
        return (BASE_NOTE,)


AbandonQuestionException = Exception
NoAnswerProvidedException = Exception
