import datetime
import logging
import os
import PogoOCR
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from discord import ApplicationContext, Attachment, Option, WebhookMessage, slash_command
from discord.embeds import Embed
from discord.ext.commands import (
    BadArgument,
    Bot,
    Cog,
    Context,
    group as old_group,
    command as old_command,
)
from discord.message import Message
from discord.utils import snowflake_time

from trainerdex_discord_bot import converters
from trainerdex_discord_bot.constants import POGOOCR_TOKEN_PATH
from trainerdex_discord_bot.embeds import ProfileCard
from trainerdex_discord_bot.utils import chat_formatting

if TYPE_CHECKING:
    from trainerdex.client import Client
    from trainerdex.trainer import Trainer
    from trainerdex.update import Update
    from trainerdex_discord_bot.config import Config
    from trainerdex_discord_bot.datatypes import Common

logger: logging.Logger = logging.getLogger(__name__)


class PostCog(Cog):
    def __init__(self, common: "Common") -> None:
        logger.info("Initializing Post cog...")
        self._common: Common = common
        self.bot: Bot = common.bot
        self.config: Config = common.config
        self.client: Client = common.client

        assert os.path.isfile(POGOOCR_TOKEN_PATH)  # Looks for a Google Cloud Token

    @slash_command(
        name="update",
        description="Update your stats with an image, optionally a few other stats are included.",
    )
    async def update_via_slash_command(
        self, ctx: ApplicationContext, image: Attachment, gold_gym_badges: Optional[int]
    ) -> None:
        if not image.content_type.startswith("image/"):
            await ctx.respond(
                "That's not an image. I can't do anything with that.", ephemeral=True
            )
            return

        await ctx.defer()

        try:
            trainer: Trainer = await converters.TrainerConverter().convert(
                None, ctx.interaction.user, cli=self.client
            )
        except BadArgument:
            await ctx.followup.send(
                chat_formatting.warning(
                    "You're not set up with a TrainerDex profile. Please ask a mod to set you up."
                ),
                ephemeral=image.ephemeral,
            )
            return

        ocr: PogoOCR.ProfileSelf = PogoOCR.ProfileSelf(
            POGOOCR_TOKEN_PATH, image_uri=image.proxy_url
        )

        try:
            ocr.get_text()
        except PogoOCR.OutOfRetriesException:
            await ctx.followup.send(
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
        stats_to_update: dict[str, Decimal | int] = {
            k: v for k, v in data_found.items() if v is not None
        }

        if not stats_to_update:
            await ctx.followup.send(
                chat_formatting.error(
                    "OCR Failed to find any stats from yours screenshot. Please try a *new* screenshot."
                )
            )
            return

        if gold_gym_badges is not None:
            stats_to_update["gymbadges_gold"] = gold_gym_badges

        await trainer.fetch_updates()
        latest_update: Update = trainer.get_latest_update()

        # If the latest update is less than half an hour old, update in place.
        print(f"{latest_update.update_time} {snowflake_time(ctx.interaction.id)}")
        if latest_update.update_time > snowflake_time(ctx.interaction.id) - datetime.timedelta(
            minutes=30
        ):
            await latest_update.edit(
                update_time=snowflake_time(ctx.interaction.id), **stats_to_update
            )
            update = latest_update
            await ctx.followup.send(
                chat_formatting.success(
                    "It looks like you've posted in the last 30 minutes so I have updated your stats in place."
                ),
                ephemeral=image.ephemeral,
            )
        else:
            # Otherwise, check that stats have changed since then.
            for stat, value in stats_to_update.items():
                if getattr(latest_update, stat) != value:
                    break
                else:
                    await ctx.followup.send(
                        chat_formatting.error(
                            "At a quick glance, it looks like your stats haven't changed since your last update. Eek!\nDid you upload an old screenshot?"
                        ),
                        ephemeral=image.ephemeral,
                    )
                    return

            # If they have, create a new update.
            update: Update = await trainer.post(
                stats=stats_to_update,
                data_source="ss_ocr",
                update_time=snowflake_time(ctx.interaction.id),
            )

        embed: ProfileCard = await ProfileCard(self._common, ctx, trainer=trainer, update=update)
        response: WebhookMessage = await ctx.followup.send(
            content=chat_formatting.loading("Checking progress…"),
            embed=embed,
            ephemeral=image.ephemeral,
        )
        await embed.show_progress()
        await response.edit(
            content=chat_formatting.loading("Loading leaderboards…"),
            embed=embed,
        )
        await embed.add_leaderboard()
        if ctx.guild:
            await response.edit(embed=embed)
            await embed.add_guild_leaderboard(ctx.guild)
        await response.edit(content=None, embed=embed)
