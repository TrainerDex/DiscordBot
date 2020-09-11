from typing import Union

import discord

from redbot.core import commands
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf

import trainerdex as client

_ = Translator("TrainerDex", __file__)


def check_xp(x: client.Update) -> int:
    if x.total_xp is None:
        return 0
    return x.total_xp


def append_twitter(text: str) -> str:
    TWITTER_MESSAGE = cf.info(
        _("If that doesn't look right, please contact us on Twitter. {twitter_handle}")
    ).format(twitter_handle="@TrainerDexApp")
    return f"{text}\n\n{TWITTER_MESSAGE}"


def append_icon(icon: Union[discord.Emoji, str], text: str) -> str:
    return f"{icon} {text}" if icon else text


def quote(text: str) -> str:
    return "\n".join(["> " + x for x in text.splitlines()])


def loading(text: str) -> str:
    """Get text prefixed with a loading emoji if the bot has access to it.

    Returns
    -------
    str
    The new message.

    """

    emoji = "<a:loading:471298325904359434>"
    return append_icon(emoji, text)


def success(text: str) -> str:
    """Get text prefixed with a white checkmark.

    Returns
    -------
    str
    The new message.

    """
    emoji = "\N{WHITE HEAVY CHECK MARK}"
    return append_icon(emoji, text)


def introduction_notes(
    ctx: commands.Context, member: discord.Member, trainer: client.Trainer, additional_message: str
) -> str:
    BASE_NOTE = _(
        """**You're getting this message because you have been added to the TrainerDex database.**

This would likely be in response to you joining `{server.name}` and posting your screenshots for a mod to approve.

TrainerDex is a Pokémon Go trainer database and leaderboard. View our privacy policy here:
<{privacy_policy_url}>

{is_visible_note}

If you have any questions, please contact us on Twitter (<{twitter_handle}>), ask the mod who approved you ({mod.mention}), or visit the TrainerDex Support Discord (<{invite_url}>)
"""
    )
    IS_VISIBLE_TRUE = _(
        """Your profile is currently visible. To hide your data from other users, please run the following command in this chat:
    `{p}profile edit visible false`"""
    )
    IS_VISIBLE_FALSE = _(
        """Your profile is not currently visible. To allow your data to be used, please run the following command in this chat:
    `{p}profile edit visible true`"""
    )
    BASE_NOTE = BASE_NOTE.format(
        server=ctx.guild,
        mod=ctx.author,
        privacy_policy_url="https://blog.trainerdex.co.uk/privacy-policy/",
        is_visible_note=(IS_VISIBLE_TRUE if trainer.is_visible else IS_VISIBLE_FALSE).format(
            p=ctx.prefix
        ),
        twitter_handle="https://twitter.com/TrainerDexApp",
        invite_url="https://discord.gg/Anz3UpM",
    )

    if additional_message:
        ADDITIONAL_NOTE = _(
            "Additionally, you have a message from `{server.name}`:\n{note}"
        ).format(server=ctx.guild, note=quote(additional_message))
        return (BASE_NOTE, ADDITIONAL_NOTE)
    else:
        return (BASE_NOTE,)
