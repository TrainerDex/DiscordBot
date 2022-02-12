from typing import Callable, Optional, Union

from discord.abc import User
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.message import Message

from trainerdex.discord.constants import SOCIAL_TWITTER
from trainerdex.discord.utils import chat_formatting
from trainerdex.trainer import Trainer


def append_twitter(text: str) -> str:
    return f"{text}\n\nIf that doesn't look right, please contact us on Twitter. {SOCIAL_TWITTER}"


def introduction_notes(
    ctx: commands.Context, member: User, trainer: Trainer, additional_message: str
) -> str:
    BASE_NOTE = """**You're getting this message because you have been added to the TrainerDex database.**

This would likely be in response to you joining `{server.name}` and posting your screenshots for a mod to approve.

TrainerDex is a Pokémon Go trainer database and leaderboard. View our privacy policy here:
<{privacy_policy_url}>

{is_visible_note}

If you have any questions, please contact us on Twitter (<{twitter_handle}>), ask the mod who approved you ({mod.mention}), or visit the TrainerDex Support Discord (<{invite_url}>)
"""
    IS_VISIBLE_TRUE = """Your profile is currently visible. To hide your data from other users, please run the following command in this chat:
    `{p}profile edit visible false`"""
    IS_VISIBLE_FALSE = """Your profile is not currently visible. To allow your data to be used, please run the following command in this chat:
    `{p}profile edit visible true`"""
    BASE_NOTE = BASE_NOTE.format(
        server=ctx.guild,
        mod=ctx.author,
        privacy_policy_url="https://trainerdex.app/legal/privacy/",
        is_visible_note=(IS_VISIBLE_TRUE if trainer.is_visible else IS_VISIBLE_FALSE).format(
            p=ctx.prefix
        ),
        twitter_handle="https://twitter.com/TrainerDexApp",
        invite_url="https://discord.trainerdex.app/",
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


class Question:
    def __init__(
        self,
        ctx: Context,
        question: str,
        message: Optional[Message] = None,
        predicate: Optional[Callable] = None,
    ) -> None:
        self._ctx: Context = ctx
        self.question: str = question
        self.message: Message = message
        self.predicate: Callable = predicate  # FIXME
        self.response: Message = None

    async def ask(self) -> str:
        if self.message:
            await self.message.edit(
                content=chat_formatting.question(f"{self._ctx.author.mention}: {self.question}")
            )
        else:
            self.message: Message = await self._ctx.send(
                content=chat_formatting.question(f"{self._ctx.author.mention}: {self.question}")
            )
        self.response: Message = await self._ctx.bot.wait_for("message", check=self.predicate)
        if self.response.content.lower() == f"{self._ctx.prefix}cancel":
            # TODO: Make an actual exception class
            raise AbandonQuestionException
        else:
            return self.answer

    async def append_answer(self, answer: Optional[str] = None) -> None:
        content: str = "{q}\n{a}".format(
            q=self.question,
            a=chat_formatting.quote(str(answer) if answer is not None else self.answer),
        )
        await self.message.edit(content=content)

    @property
    def answer(self) -> Union[str, None]:
        if self.response:
            return self.response.content
        return None
