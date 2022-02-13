from __future__ import annotations

import contextlib
import datetime
import humanize
import logging
import os
import PogoOCR
from decimal import Decimal
from typing import TYPE_CHECKING

from discord.embeds import Embed
from discord.errors import DiscordException
from discord.ext.commands import (
    BadArgument,
    Bot,
    Cog,
    Context,
    group as old_group,
    command as old_command,
)
from discord.message import Message

from trainerdex_discord_bot import converters
from trainerdex_discord_bot.constants import POGOOCR_TOKEN_PATH, CustomEmoji
from trainerdex_discord_bot.embeds import ProfileCard
from trainerdex_discord_bot.utils import chat_formatting
from trainerdex_discord_bot.utils.general import append_twitter

if TYPE_CHECKING:
    from trainerdex.client import Client
    from trainerdex.trainer import Trainer
    from trainerdex.update import Update
    from trainerdex_discord_bot.config import Config
    from trainerdex_discord_bot.datatypes import ChannelConfig, Common, GuildConfig

logger: logging.Logger = logging.getLogger(__name__)


class PostCog(Cog):
    def __init__(self, common: Common) -> None:
        logger.info("Initializing Post cog...")
        self._common: Common = common
        self.bot: Bot = common.bot
        self.config: Config = common.config
        self.client: Client = common.client

        assert os.path.isfile(POGOOCR_TOKEN_PATH)  # Looks for a Google Cloud Token

    @Cog.listener("on_message")
    async def check_screenshot(self, message: Message) -> None:
        guild_config: GuildConfig = self.config.get_guild(message.guild)
        channel_config: ChannelConfig = self.config.get_channel(message.channel)

        if not guild_config.enabled:
            return

        if not channel_config.profile_ocr:
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
            await message.add_reaction(CustomEmoji.LOADING.value)

        try:
            trainer: Trainer = await converters.TrainerConverter().convert(
                None, message.author, cli=self.client
            )
        except BadArgument:
            with contextlib.suppress(DiscordException):
                await message.remove_reaction(CustomEmoji.LOADING.value, self.bot.user)
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
                    content=append_twitter(chat_formatting.loading("Just processing that now…"))
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
                        await message.remove_reaction(CustomEmoji.LOADING.value, self.bot.user)
                        await message.add_reaction("\N{WARNING SIGN}\N{VARIATION SELECTOR-16}")
                        return
                elif latest_update.total_xp == data_found.get("total_xp"):
                    text: str = chat_formatting.warning(
                        "You've already set your XP to this figure. "
                        "In future, to see the output again, please run the `progress` command as it costs us to run OCR."
                    )
                    with contextlib.suppress(DiscordException):
                        await message.remove_reaction(CustomEmoji.LOADING.value, self.bot.user)
                        await message.add_reaction("\N{WARNING SIGN}\N{VARIATION SELECTOR-16}")
                else:
                    await trainer.post(
                        stats=data_found,
                        data_source="ss_ocr",
                        update_time=message.created_at,
                    )
                    with contextlib.suppress(DiscordException):
                        await message.remove_reaction(CustomEmoji.LOADING.value, self.bot.user)
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
                    self._common,
                    message,
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
                    await message.remove_reaction(CustomEmoji.LOADING.value, self.bot.user)
                    await message.add_reaction("\N{THUMBS DOWN SIGN}")

    @old_group(name="update", case_insensitive=True)
    async def update(self, ctx: Context) -> None:
        pass

    @old_command(
        name="gyms", brief="Run this after posting your XP for the best results.", hidden=True
    )
    async def post__gyms(
        self,
        ctx: Context,
        value: int,
    ) -> None:
        async with ctx.typing():
            try:
                trainer: Trainer = await converters.TrainerConverter().convert(
                    ctx, ctx.author, cli=self.client
                )
            except BadArgument:
                await ctx.send(chat_formatting.error("No profile found."))
                return

            await trainer.fetch_updates()
            latest_update: Update = trainer.get_latest_update()
            if latest_update and latest_update.update_time > (
                datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(hours=12)
            ):
                if latest_update.gymbadges_gold:
                    post_new: bool = True
                else:
                    post_new: bool = False
                    update: Update = latest_update
            else:
                post_new: bool = True

            if post_new:
                message: Message = await ctx.send(chat_formatting.loading("Creating a new post…"))
                update: Update = await trainer.post(
                    stats={"gymbadges_gold": value},
                    data_source="ts_social_discord",
                    update_time=ctx.message.created_at,
                    submission_date=datetime.datetime.now(tz=datetime.timezone.utc),
                )
            else:
                message: Message = await ctx.send(
                    chat_formatting.loading("Updating a post from earlier today…")
                )
                await update.edit(
                    **{"update_time": ctx.message.created_at, "gymbadges_gold": value}
                )

            if ctx.guild and not trainer.is_visible:
                await message.edit("Sending in DMs")
                message: Message = await ctx.author.send(
                    content=chat_formatting.loading("Loading output…")
                )

            await message.edit(content=chat_formatting.loading("Loading output…"))
            embed: Embed = await ProfileCard(
                self._common,
                ctx,
                trainer=trainer,
                update=update,
            )
            await message.edit(content=chat_formatting.loading("Loading output…"))
            await embed.show_progress()
            await message.edit(
                content=chat_formatting.loading("Loading output…"),
                embed=embed,
            )
            await embed.add_leaderboard()
            if ctx.guild:
                await message.edit(embed=embed)
                await embed.add_guild_leaderboard(ctx.guild)
            await message.edit(content=None, embed=embed)
