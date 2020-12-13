from typing import Callable, Optional, Union

import discord
from redbot.core import commands
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf
from redbot.core.utils import predicates
from trainerdex.trainer import Trainer

_ = Translator("TrainerDex", __file__)


def append_twitter(text: str) -> str:
    TWITTER_MESSAGE = cf.info(
        _("If that doesn't look right, please contact us on Twitter. {twitter_handle}")
    ).format(twitter_handle="@TrainerDexApp")
    return f"{text}\n\n{TWITTER_MESSAGE}"


def append_icon(icon: Union[discord.Emoji, str], text: str) -> str:
    return f"{icon} {text}" if icon else text


def quote(text: str) -> str:
    return "> " + text.rstrip("\n").replace("\n", "\n> ")


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
    ctx: commands.Context, member: discord.Member, trainer: Trainer, additional_message: str
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


AbandonQuestionException = Exception
NoAnswerProvidedException = Exception


class Question:
    def __init__(
        self,
        ctx: commands.Context,
        question: str,
        message: Optional[discord.Message] = None,
        predicate: Optional[Callable] = None,
    ) -> None:
        self._ctx: commands.Context = ctx
        self.question: str = question
        self.message: discord.Message = message
        self.predicate: Callable = predicate or predicates.MessagePredicate.same_context(self._ctx)
        self.response: discord.Message = None

    async def ask(self) -> Union[str, None]:
        if self.message:
            await self.message.edit(
                content=cf.question(f"{self._ctx.author.mention}: {self.question}")
            )
        else:
            self.message = await self._ctx.send(
                content=cf.question(f"{self._ctx.author.mention}: {self.question}")
            )
        self.response = await self._ctx.bot.wait_for("message", check=self.predicate)
        if self.response.content.lower() == f"{self._ctx.prefix}cancel":
            # TODO: Make an actual exception class
            raise AbandonQuestionException
        else:
            return self.answer

    async def append_answer(self, answer: Optional[str] = None) -> None:
        content = "{q}\n{a}".format(
            q=self.question, a=quote(str(answer) if answer is not None else self.answer)
        )
        await self.message.edit(content=content)

    @property
    def answer(self) -> Union[str, None]:
        if self.response:
            return self.response.content
        return None
