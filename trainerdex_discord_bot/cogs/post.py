import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Mapping, NoReturn, Optional

from discord import (
    ApplicationContext,
    Attachment,
    Message,
    Option,
    OptionChoice,
    slash_command,
)
from discord.utils import snowflake_time
from google.oauth2 import service_account
from PogoOCR import OCRClient, Screenshot, ScreenshotClass
from PogoOCR.providers import Providers

from trainerdex_discord_bot.cogs.interface import Cog
from trainerdex_discord_bot.config import TokenDocuments
from trainerdex_discord_bot.embeds import ProfileCard
from trainerdex_discord_bot.exceptions import CogHealthcheckException
from trainerdex_discord_bot.utils import chat_formatting
from trainerdex_discord_bot.utils.converters import get_trainer, get_trainer_from_user
from trainerdex_discord_bot.utils.general import send
from trainerdex_discord_bot.utils.validators import validate_trainer_nickname

if TYPE_CHECKING:
    from PogoOCR.images.actitvity_view import ActivityViewData
    from trainerdex.trainer import Trainer
    from trainerdex.update import Update


class PostCog(Cog):
    async def _healthcheck(self) -> NoReturn | None:
        token = await self.config.get_token(TokenDocuments.GOOGLE.value)
        if token is None:
            raise CogHealthcheckException("Google Cloud token not found.")
        else:
            await self._load_ocr_client(token)

    async def _load_ocr_client(self, token: Mapping) -> None:
        credentials: service_account.Credentials = (
            service_account.Credentials.from_service_account_info(token)
        )
        self.ocr = OCRClient(credentials=credentials, provider=Providers.GOOGLE)

    @slash_command(
        name="update",
        description="Update your stats with an image, optionally a few other stats are included.",
    )
    async def update_via_slash_command(
        self, ctx: ApplicationContext, image: Attachment, gold_gym_badges: Optional[int]
    ) -> None:
        if not image.content_type.startswith("image/"):
            await send(ctx, "That's not an image. I can't do anything with that.", ephemeral=True)
            return

        await ctx.defer()

        await send(
            ctx,
            content=chat_formatting.info(
                f"{ctx.interaction.user.mention} shared an image for use with `/{ctx.command.qualified_name}`."
            ),
            file=await image.to_file(),
        )

        trainer: Trainer = await get_trainer_from_user(self.client, ctx.interaction.user)
        if trainer is None:
            await send(
                ctx,
                chat_formatting.warning(
                    "You're not set up with a TrainerDex profile. Please ask a mod to set you up."
                ),
                ephemeral=image.ephemeral,
            )
            return

        screenshot = await Screenshot.from_url(
            image.url,
            klass=ScreenshotClass.ACTIVITY_VIEW,
            asyncronous=True,
        )

        request = self.ocr.open_request(screenshot)
        result: ActivityViewData = self.ocr.process_ocr(request)

        data_found: dict[str, Decimal | int | None] = {
            "travel_km": result.travel_km,
            "capture_total": result.capture_total,
            "pokestops_visited": result.pokestops_visited,
            "total_xp": result.total_xp,
        }
        stats_to_update: dict[str, Decimal | int] = {
            k: v for k, v in data_found.items() if v is not None
        }

        if not stats_to_update:
            await send(
                ctx,
                chat_formatting.error(
                    "OCR Failed to find any stats from your screenshot. Please try a *new* screenshot."
                ),
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
            await send(
                ctx,
                chat_formatting.success(
                    "It looks like you've posted in the last 30 minutes so I have updated your stats in place."
                ),
            )
        else:
            # Otherwise, check that stats have changed since then.
            for stat, value in stats_to_update.items():
                if getattr(latest_update, stat) != value:
                    break
            else:
                await send(
                    ctx,
                    chat_formatting.error(
                        "At a quick glance, it looks like your stats haven't changed since your last update. Eek!\nDid you upload an old screenshot?"
                    ),
                )
                return

            # If they have, create a new update.
            update: Update = await trainer.post(
                stats=stats_to_update,
                data_source="ss_ocr",
                update_time=snowflake_time(ctx.interaction.id),
            )

        embed: ProfileCard = await ProfileCard(self._common, ctx, trainer=trainer, update=update)
        response: Message = await send(
            ctx,
            content=chat_formatting.loading("Checking progress…"),
            embed=embed,
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

    @slash_command(
        name="register",
        options=[
            Option(
                Attachment,
                name="image",
                description="An image of your Pokemon Go profile.",
                required=True,
            ),
            Option(
                str,
                name="nickname",
                description="Your Pokemon Go nickname.",
                required=True,
            ),
            Option(
                int,
                name="team",
                description="The user's Pokemon Go team",
                choices=[
                    OptionChoice("No Team", 0),
                    OptionChoice("Mystic", 1),
                    OptionChoice("Valor", 2),
                    OptionChoice("Instinct", 3),
                ],
                required=False,
            ),
            Option(int, name="total_xp", required=False),
            # Option(int, name="level", required=False),
            Option(float, name="travel_km", required=False),
            Option(int, name="capture_total", required=False),
            Option(int, name="pokestops_visited", required=False),
            Option(int, name="gold_gym_badges", required=False),
        ],
    )
    async def create_profile(
        self,
        ctx: ApplicationContext,
        image: Attachment,
        nickname: str,
        team: Optional[int] = None,
        total_xp: Optional[int] = None,
        # level: Optional[int] = None,
        travel_km: Optional[float] = None,
        capture_total: Optional[int] = None,
        pokestops_visited: Optional[int] = None,
        gold_gym_badges: Optional[int] = None,
    ):
        if not image.content_type.startswith("image/"):
            await send(ctx, "That's not a valid image.", ephemeral=True)
            return

        if await get_trainer(self.client, user=ctx.author, nickname=nickname) is not None:
            await send(
                ctx,
                chat_formatting.error("Unable to create a profile. You may already have one."),
                ephemeral=True,
            )
            return

        await ctx.defer()

        await send(
            ctx,
            content=chat_formatting.info(
                f"{ctx.interaction.user.mention} shared an image for use with `/{ctx.command.qualified_name}`."
            ),
            file=await image.to_file(),
        )

        screenshot = await Screenshot.from_url(
            image.url,
            klass=ScreenshotClass.ACTIVITY_VIEW,
            asyncronous=True,
        )

        request = self.ocr.open_request(screenshot)
        result: ActivityViewData = self.ocr.process_ocr(request)

        print(result)
        profile_data = {
            "username": result.username or nickname,
            "faction": result.faction and result.faction.id or team,
        }
        print(profile_data)

        if not validate_trainer_nickname(profile_data["username"]):
            await send(
                ctx,
                chat_formatting.error("Unable to create a profile. Your nickname is invalid."),
                ephemeral=True,
            )
            return

        update_data = {
            "total_xp": result.total_xp or total_xp,
            "travel_km": result.travel_km or travel_km,
            "capture_total": result.capture_total or capture_total,
            "pokestops_visited": result.pokestops_visited or pokestops_visited,
            "gold_gym_badges": gold_gym_badges,
        }
        print(update_data)

        if not update_data.get("total_xp"):
            await send(
                ctx,
                chat_formatting.error(
                    "Failed to pull Total XP from your screenshot and it wasn't provided in the command. "
                    "Please try again specifiying it in the command or using a new screenshot."
                ),
            )
            return

        trainer: Trainer = await self.client.create_trainer(**profile_data)
        print(trainer)
        user = await trainer.user()
        await user.add_discord(ctx.author)

        update: Update = await trainer.post(
            data_source="ss_registration",
            stats=update_data,
            update_time=snowflake_time(ctx.interaction.id),
        )
        print(update)

        message = await send(
            ctx, chat_formatting.success(f"Profile created for {ctx.author.mention}.")
        )
        embed: ProfileCard = await ProfileCard(self._common, ctx, trainer=trainer, update=update)

        await message.edit(embed=embed)
