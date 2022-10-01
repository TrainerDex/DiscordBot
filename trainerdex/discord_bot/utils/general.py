from datetime import datetime, timedelta
from typing import List, Optional, Sequence, Union, overload
from zoneinfo import ZoneInfo

from discord import (
    AllowedMentions,
    ApplicationContext,
    Embed,
    File,
    GuildSticker,
    HTTPException,
    Interaction,
    InteractionResponded,
    Message,
    MessageReference,
    PartialMessage,
    StickerItem,
)
from discord.abc import Messageable, User
from discord.ui.view import View
from trainerdex.api.trainer import Trainer
from yarl import URL

from trainerdex.discord_bot.constants import SOCIAL_TWITTER
from trainerdex.discord_bot.utils import chat_formatting


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


@overload
async def send(
    destination: ApplicationContext | Messageable,
    content: Optional[str] = ...,
    *,
    tts: bool = ...,
    embed: Embed = ...,
    file: File = ...,
    stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
    delete_after: float = ...,
    nonce: Union[str, int] = ...,
    allowed_mentions: AllowedMentions = ...,
    reference: Union[Message, MessageReference, PartialMessage] = ...,
    mention_author: bool = ...,
    view: View = ...,
) -> Message:
    ...


@overload
async def send(
    destination: ApplicationContext | Messageable,
    content: Optional[str] = ...,
    *,
    tts: bool = ...,
    embed: Embed = ...,
    files: List[File] = ...,
    stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
    delete_after: float = ...,
    nonce: Union[str, int] = ...,
    allowed_mentions: AllowedMentions = ...,
    reference: Union[Message, MessageReference, PartialMessage] = ...,
    mention_author: bool = ...,
    view: View = ...,
) -> Message:
    ...


@overload
async def send(
    destination: ApplicationContext | Messageable,
    content: Optional[str] = ...,
    *,
    tts: bool = ...,
    embeds: List[Embed] = ...,
    file: File = ...,
    stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
    delete_after: float = ...,
    nonce: Union[str, int] = ...,
    allowed_mentions: AllowedMentions = ...,
    reference: Union[Message, MessageReference, PartialMessage] = ...,
    mention_author: bool = ...,
    view: View = ...,
) -> Message:
    ...


@overload
async def send(
    destination: ApplicationContext | Messageable,
    content: Optional[str] = ...,
    *,
    tts: bool = ...,
    embeds: List[Embed] = ...,
    files: List[File] = ...,
    stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
    delete_after: float = ...,
    nonce: Union[str, int] = ...,
    allowed_mentions: AllowedMentions = ...,
    reference: Union[Message, MessageReference, PartialMessage] = ...,
    mention_author: bool = ...,
    view: View = ...,
) -> Message:
    ...


async def send(
    destination: ApplicationContext | Messageable, content=None, *args, **kwargs
) -> Message:
    """A utility function to send a message to a destination.

    Always returning a subclass of Message."""
    if isinstance(destination, ApplicationContext):
        try:
            response = await destination.respond(content=content, *args, **kwargs)
        except (HTTPException, TypeError, ValueError, InteractionResponded):
            return await destination.followup.send(content=content, *args, **kwargs)

        if isinstance(response, Message):
            return response
        elif isinstance(response, Interaction):
            return await response.original_message()
    else:
        return await destination.send(content=content, *args, **kwargs)


def google_calendar_link_for_datetime(dt: datetime) -> str:
    """Return a Google Calendar link for a datetime."""

    path = URL("http://www.google.com/calendar/event")

    # Format date as YYYYMMDDTHHMMSSZ
    print(dt)
    dt = dt.astimezone(ZoneInfo("UTC"))
    print(dt)

    start_time = (dt - timedelta(minutes=15)).strftime("%Y%m%dT%H%M%SZ")
    end_time = dt.strftime("%Y%m%dT%H%M%SZ")

    return path % {
        "action": "TEMPLATE",
        "text": f"TrainerDex Leaderboards Deadline: Week {dt.strftime('%V')}",
        "dates": f"{start_time}/{end_time}",
        "details": "The deadline for submitting your screenshots for the TrainerDex Leaderboards for this week.",
        "location": "https://trainerdex.app/new/",
    }
