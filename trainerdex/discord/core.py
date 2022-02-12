import contextlib
import humanize
import logging
import os
import PogoOCR
from abc import ABC
from decimal import Decimal

from discord.activity import Game
from discord.errors import DiscordException
from discord.ext.commands import BadArgument, Bot, Cog
from discord.message import Message

from trainerdex.client import Client
from trainerdex.trainer import Trainer
from trainerdex.update import Update
from trainerdex.discord import __version__, converters
from trainerdex.discord.config import Config
from trainerdex.discord.constants import POGOOCR_TOKEN_PATH, TRAINERDEX_API_TOKEN, CUSTOM_EMOJI
from trainerdex.discord.embeds import ProfileCard
from trainerdex.discord.datatypes import ChannelConfig, GuildConfig
from trainerdex.discord.leaderboard import Leaderboard
from trainerdex.discord.mod import ModCmds
from trainerdex.discord.post import Post
from trainerdex.discord.profile import Profile
from trainerdex.discord.settings import Settings
from trainerdex.discord.utils import chat_formatting
from trainerdex.discord.utils.general import append_twitter

logger: logging.Logger = logging.getLogger(__name__)


class CompositeMetaClass(type(Cog), type(ABC)):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """

    pass


class TrainerDex(ModCmds, Post, Profile, Leaderboard, Settings, Cog, metaclass=CompositeMetaClass):
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.config: Config = Config()
        self.client: Client = None
        self.bot.loop.create_task(self.create_client())
        self.bot.loop.create_task(self.set_game_to_version())

        assert os.path.isfile(POGOOCR_TOKEN_PATH)  # Looks for a Google Cloud Token

    async def set_game_to_version(self) -> None:
        await self.bot.wait_until_ready()
        await self.bot.change_presence(activity=Game(name=__version__))

    async def create_client(self) -> None:
        self.client: Client = Client(token=TRAINERDEX_API_TOKEN)

    @Cog.listener("on_message_without_command")
    async def check_screenshot(self, message: Message) -> None:
        guild_config: GuildConfig = self.config.get_guild(message.guild)
        channel_config: ChannelConfig = self.config.get_channel(message.channel)

        if not guild_config.enabled or not channel_config.profile_ocr:
            return

        if len(message.attachments) != 1:
            # TODO: Enable multiple images
            return

        if os.path.splitext(message.attachments[0].proxy_url)[1].lower() not in [
            ".jpeg",
            ".jpg",
            ".png",
        ]:
            return

        with contextlib.suppress(DiscordException):
            await message.add_reaction(self.bot.get_emoji(CUSTOM_EMOJI.LOADING))

        try:
            trainer: Trainer = await converters.TrainerConverter().convert(
                None, message.author, cli=self.client
            )
        except BadArgument:
            with contextlib.suppress(DiscordException):
                await message.remove_reaction(
                    self.bot.get_emoji(CUSTOM_EMOJI.LOADING), self.bot.user
                )
                await message.add_reaction("\N{THUMBS DOWN SIGN}")
            await message.reply(
                "No TrainerDex profile found for this Discord account. A moderator for this server can set you up."
            )
            return

        async with message.channel.typing():
            reply: Message = await message.reply(
                chat_formatting.loading("That's a nice image you have there, let's see…")
            )
            ocr: PogoOCR.ProfileSelf = PogoOCR.ProfileSelf(
                POGOOCR_TOKEN_PATH, image_uri=message.attachments[0].proxy_url
            )

            try:
                ocr.get_text()
            except PogoOCR.OutOfRetriesException:
                await reply.edit(
                    chat_formatting.error(
                        "OCR Failed to recognise text from screenshot. Please try a *new* screenshot."
                    )
                )
                return

            data_found: dict[str, Decimal | int | None] = {
                "travel_km": ocr.travel_km,
                "capture_total": ocr.capture_total,
                "pokestops_visited": ocr.pokestops_visited,
                "total_xp": ocr.total_xp,
            }

            if data_found.get("total_xp"):
                await reply.edit(
                    content=append_twitter(
                        chat_formatting.loading(
                            "We found the following stats:\n {stats}\nJust processing that now…"
                        ).format(stats=chat_formatting.box(data_found))
                    )
                )
                await trainer.fetch_updates()
                latest_update: Update = trainer.get_latest_update_for_stat("total_xp")
                if latest_update.total_xp > data_found.get("total_xp"):
                    await reply.edit(
                        content=append_twitter(
                            chat_formatting.warning(
                                "You've previously set your XP to higher than what you're trying to set it to. "
                                "It's currently set to {xp}."
                            )
                        ).format(xp=humanize.intcomma(latest_update.total_xp))
                    )
                    with contextlib.suppress(DiscordException):
                        await message.remove_reaction(
                            self.bot.get_emoji(CUSTOM_EMOJI.LOADING), self.bot.user
                        )
                        await message.add_reaction("\N{WARNING SIGN}\N{VARIATION SELECTOR-16}")
                        return
                elif latest_update.total_xp == data_found.get("total_xp"):
                    text: str = chat_formatting.warning(
                        "You've already set your XP to this figure. "
                        "In future, to see the output again, please run the `progress` command as it costs us to run OCR."
                    )
                    with contextlib.suppress(DiscordException):
                        await message.remove_reaction(
                            self.bot.get_emoji(CUSTOM_EMOJI.LOADING), self.bot.user
                        )
                        await message.add_reaction("\N{WARNING SIGN}\N{VARIATION SELECTOR-16}")
                else:
                    await trainer.post(
                        stats=data_found,
                        data_source="ss_ocr",
                        update_time=message.created_at,
                    )
                    with contextlib.suppress(DiscordException):
                        await message.remove_reaction(
                            self.bot.get_emoji(CUSTOM_EMOJI.LOADING), self.bot.user
                        )
                        await message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
                    text = None
                if message.guild and not trainer.is_visible:
                    await reply.edit("Sending in DMs")
                    reply: Message = await message.author.send(
                        content=chat_formatting.loading("Loading output…")
                    )
                await reply.edit(
                    content="\n".join(
                        [
                            x
                            for x in [text, chat_formatting.loading("Loading output…")]
                            if x is not None
                        ]
                    )
                )
                embed: ProfileCard = await ProfileCard(
                    ctx_or_message=message,
                    bot=self.bot,
                    client=self.client,
                    trainer=trainer,
                )
                await reply.edit(
                    content="\n".join(
                        [
                            x
                            for x in [text, chat_formatting.loading("Loading output…")]
                            if x is not None
                        ]
                    )
                )
                await embed.show_progress()
                await reply.edit(
                    content="\n".join(
                        [
                            x
                            for x in [text, chat_formatting.loading("Loading leaderboards…")]
                            if x is not None
                        ]
                    ),
                    embed=embed,
                )
                await embed.add_leaderboard()
                if message.guild:
                    await reply.edit(embed=embed)
                    await embed.add_guild_leaderboard(message.guild)
                await reply.edit(content=text, embed=embed)
            else:
                await reply.edit(
                    content=chat_formatting.error("I could not find Total XP in your image. ")
                    + "\n\n"
                    + chat_formatting.info(
                        "We use Google Vision API to read your images. "
                        "Please ensure that the ‘Total XP’ field is visible. "
                        "If it is visible and your image still doesn't scan after a minute, try a new image. "
                        "Posting the same image again, will likely cause another failure."
                    )
                )
                with contextlib.suppress(DiscordException):
                    await message.remove_reaction(
                        self.bot.get_emoji(CUSTOM_EMOJI.LOADING), self.bot.user
                    )
                    await message.add_reaction("\N{THUMBS DOWN SIGN}")
