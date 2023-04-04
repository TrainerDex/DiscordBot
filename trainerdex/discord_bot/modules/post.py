import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Dict

from discord import ApplicationContext, Attachment, Message, Option, slash_command
from discord.utils import snowflake_time
from trainerdex.api.exceptions import HTTPException

from trainerdex.discord_bot.constants import STAT_MAP
from trainerdex.discord_bot.embeds import ProfileCard
from trainerdex.discord_bot.modules.base import Module
from trainerdex.discord_bot.ocr import OCRClient
from trainerdex.discord_bot.utils import chat_formatting
from trainerdex.discord_bot.utils.converters import get_trainer_from_user

if TYPE_CHECKING:
    from trainerdex.api.trainer import Trainer
    from trainerdex.api.update import Update


class PostModule(Module):
    @classmethod
    @property
    def METADATA_ID(cls) -> str:
        return "PostCog"

    @slash_command(
        name="update",
        description="Update your stats with an image, optionally a few other stats are included.",
        options=[
            Option(
                Attachment,
                name="image",
                description="Image for OCR",
                required=False,
            ),
            Option(int, name="total_xp", description="Total XP", required=False),
            Option(int, name="pokestops_visited", description="Backpacker", required=False),
            Option(int, name="capture_total", description="Collector", required=False),
            Option(float, name="travel_km", description="Jogger", required=False),
            Option(int, name="gym_gold", description="Gold Gym Badges", required=False),
            Option(int, name="unique_pokestops", description="Sightseer", required=False),
            Option(int, name="legendary_battle_won", description="Battle Legend", required=False),
            Option(int, name="raid_battle_won", description="Champion", required=False),
            Option(int, name="hours_defended", description="Gym Leader", required=False),
            Option(int, name="challenge_quests", description="Pokémon Ranger", required=False),
            Option(int, name="evolved_total", description="Scientist", required=False),
            Option(int, name="trading_distance", description="Pilot", required=False),
            Option(int, name="hatched_total", description="Breeder", required=False),
            Option(int, name="rocket_grunts_defeated", description="Hero", required=False),
            Option(int, name="trading", description="Gentleman", required=False),
            Option(int, name="battle_attack_won", description="Battle Girl", required=False),
            Option(int, name="wayfarer", description="Wayfarer", required=False),
            Option(int, name="berries_fed", description="Berry Master", required=False),
            Option(int, name="buddy_best", description="Best Buddy", required=False),
            Option(int, name="great_league", description="Great League Veteran", required=False),
            Option(int, name="ultra_league", description="Ultra League Veteran", required=False),
            Option(int, name="master_league", description="Master League Veteran", required=False),
            Option(int, name="total_mega_evos", description="Successor", required=False),
            Option(int, name="seven_day_streaks", description="Triathlete", required=False),
        ],
    )
    async def update_via_slash_command(
        self,
        ctx: ApplicationContext,
        image: Attachment | None = None,
        total_xp: int | None = None,
        pokestops_visited: int | None = None,
        capture_total: int | None = None,
        travel_km: float | None = None,
        gym_gold: int | None = None,
        unique_pokestops: int | None = None,
        legendary_battle_won: int | None = None,
        raid_battle_won: int | None = None,
        hours_defended: int | None = None,
        challenge_quests: int | None = None,
        evolved_total: int | None = None,
        trading_distance: int | None = None,
        hatched_total: int | None = None,
        rocket_grunts_defeated: int | None = None,
        trading: int | None = None,
        battle_attack_won: int | None = None,
        wayfarer: int | None = None,
        berries_fed: int | None = None,
        buddy_best: int | None = None,
        great_league: int | None = None,
        ultra_league: int | None = None,
        master_league: int | None = None,
        total_mega_evos: int | None = None,
        seven_day_streaks: int | None = None,
    ) -> None:
        kwargs = locals().copy()
        kwargs.pop("self")
        kwargs.pop("ctx")
        kwargs.pop("image")
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        if image is not None and not image.content_type.startswith("image/"):
            image = None

        if not (image or kwargs):
            await ctx.interaction.response.send_message(
                (
                    "You haven't provided a valid image or any stats. Sorry, nothing I can do here. "
                    "Perhaps you forgot to attach an image?"
                ),
            )
            return

        await ctx.defer()

        if image and not kwargs:
            await ctx.send(
                content=chat_formatting.info(
                    f"{ctx.interaction.user.mention} shared an image for use with `/{ctx.command.qualified_name}`.",
                ),
                file=await image.to_file(),
            )
        elif image and kwargs:
            await ctx.send(
                content=chat_formatting.info(
                    (
                        f"{ctx.interaction.user.mention} shared an image for use with "
                        f"`/{ctx.command.qualified_name}`, "
                        f"with the following additional stats: "
                        f"{', '.join(f'`{key}: {value}`' for key, value in kwargs.items())}"
                    ),
                ),
                file=await image.to_file(),
            )
        else:
            await ctx.send(
                content=chat_formatting.info(
                    (
                        f"{ctx.interaction.user.mention} posted the following stats: "
                        f"{', '.join(f'`{key}: {value}`' for key, value in kwargs.items())}"
                    ),
                ),
            )

        trainer = None
        async with self.client() as client:
            trainer: Trainer = await get_trainer_from_user(client, ctx.interaction.user)

            if trainer is None:
                await ctx.send(
                    chat_formatting.warning("You're not set up with a TrainerDex profile."),
                )
                return

            data_from_ocr = {}
            if image is not None:
                await ctx.send("Analyzing image...", delete_after=30)
                try:
                    data_from_ocr: Dict[str, float] = await OCRClient.request_activity_view_scan(image)
                except Exception:
                    if not kwargs:
                        await ctx.send(
                            chat_formatting.error(
                                (
                                    "The OCR failed to process and you didn't provide any keywords. "
                                    "I can't do anything with that."
                                ),
                            ),
                        )
                        return
                    else:
                        await ctx.send(
                            chat_formatting.warning(
                                (
                                    "The OCR failed to process, "
                                    "but I'm still going to try to update your stats with the keywords you provided."
                                ),
                            ),
                        )

            stats_to_update = kwargs | data_from_ocr

            stats_to_update: dict[str, Decimal | int] = {
                STAT_MAP.get(key, key): value for key, value in stats_to_update.items() if value is not None
            }

            if not stats_to_update:
                await ctx.send(
                    chat_formatting.error("No stats were provided. Please provide at least one stat to update."),
                )
                return

            await trainer.fetch_updates()
            latest_update: Update = await trainer.get_latest_update()

            # If the latest update is less than half an hour old, update in place.
            if latest_update.update_time > snowflake_time(ctx.interaction.id) - datetime.timedelta(minutes=30):
                try:
                    await latest_update.edit(update_time=snowflake_time(ctx.interaction.id), **stats_to_update)
                except HTTPException as e:
                    r, data = e.args
                    if data is not None:
                        await ctx.send(
                            chat_formatting.error(
                                f"The update failed to post because of the following error: `{data}`"
                            ),
                        )
                        raise HTTPException(None, data) from e
                    else:
                        await ctx.send(
                            chat_formatting.error("The update failed to post because of an unknown error."),
                        )
                        raise HTTPException(None, data) from e

                update = latest_update
                await ctx.send(
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
                    await ctx.send(
                        chat_formatting.error(
                            (
                                "At a quick glance, it looks like your stats haven't changed since your last update."
                                " Eek!\nDid you upload an old screenshot?"
                            )
                        ),
                    )
                    return

                # If they have, create a new update.
                try:
                    update: Update = await trainer.post(
                        stats=stats_to_update,
                        data_source="ss_ocr" if data_from_ocr else "ts_social_discord",
                        update_time=snowflake_time(ctx.interaction.id),
                    )
                except HTTPException as e:
                    r, data = e.args
                    if data is not None:
                        await ctx.send(
                            chat_formatting.error(
                                f"The update failed to post because of the following error: `{data}`"
                            ),
                        )
                        raise HTTPException(None, data) from e
                    else:
                        await ctx.send(
                            chat_formatting.error("The update failed to post because of an unknown error."),
                        )
                        raise HTTPException(None, data) from e

            embed: ProfileCard = await ProfileCard(self._common, ctx, trainer=trainer, update=update)
            response: Message = await ctx.send(
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

    # @slash_command(
    #     name="register",
    #     options=[
    #         Option(
    #             Attachment,
    #             name="image",
    #             description="An image of your Pokémon Go profile.",
    #             required=True,
    #         ),
    #         Option(
    #             str,
    #             name="nickname",
    #             description="Your Pokémon Go nickname.",
    #             required=True,
    #         ),
    #         Option(
    #             int,
    #             name="team",
    #             description="Your Pokémon Go team",
    #             choices=[
    #                 OptionChoice("No Team (Grey)", 0),
    #                 OptionChoice("Mystic", 1),
    #                 OptionChoice("Valor", 2),
    #                 OptionChoice("Instinct", 3),
    #             ],
    #             required=False,
    #         ),
    #         Option(
    #             int,
    #             name="total_xp",
    #             required=False,
    #         ),
    #         Option(
    #             int,
    #             name="level",
    #             # required=False,
    #         ),
    #         Option(
    #             float,
    #             name="travel_km",
    #             required=False,
    #         ),
    #         Option(
    #             int,
    #             name="capture_total",
    #             required=False,
    #         ),
    #         Option(
    #             int,
    #             name="pokestops_visited",
    #             required=False,
    #         ),
    #     ],
    # )
    # async def create_profile(
    #     self,
    #     ctx: ApplicationContext,
    #     # image: Attachment,
    #     nickname: str,
    #     team: int,
    #     total_xp: int,
    #     # level: int,
    #     travel_km: Optional[float] = None,
    #     capture_total: Optional[int] = None,
    #     pokestops_visited: Optional[int] = None,
    # ):
    #     if not image.content_type.startswith("image/"):
    #         await ctx.interaction.response.send_message("That's not a valid image.")
    #         return

    #     async with self.client() as client:
    #         if await get_trainer(client, user=ctx.author, nickname=nickname) is not None:
    #             ctx.interaction.response.send_message(
    #                 chat_formatting.error("Unable to create a profile. You may already have one."),
    #             )
    #             return

    #     await ctx.defer()

    #     await ctx.send(
    #         content=chat_formatting.info(
    #             f"{ctx.interaction.user.mention} shared an image for use with `/{ctx.command.qualified_name}`."
    #         ),
    #         file=await image.to_file(),
    #     )

    #     screenshot = await Screenshot.from_url(
    #         image.url,
    #         klass=ScreenshotClass.ACTIVITY_VIEW,
    #         asyncronous=True,
    #     )

    #     request = self.ocr.open_request(screenshot)
    #     result = self.ocr.process_ocr(request)

    #     profile_data = {
    #         "username": nickname,  # result.username or nickname,
    #         "faction": team,  # result.faction and result.faction.id or team,
    #     }

    #     if not validate_trainer_nickname(profile_data["username"]):
    #         await ctx.send(
    #             chat_formatting.error("Unable to create a profile. Your nickname is invalid."),
    #         )
    #         return

    #     update_data = {
    #         "total_xp": total_xp,  # result.total_xp or total_xp,
    #         "travel_km": travel_km,  # result.travel_km or travel_km,
    #         "capture_total": capture_total,  # result.capture_total or capture_total,
    #         "pokestops_visited": pokestops_visited,  # result.pokestops_visited or pokestops_visited,
    #         "gold_gym_badges": gold_gym_badges,
    #     }

    #     if not update_data.get("total_xp"):
    #         await ctx.send(
    #             chat_formatting.error(
    #                 "Failed to pull Total XP from your screenshot and it wasn't provided in the command. "
    #                 "Please try again specifiying it in the command or using a new screenshot."
    #             ),
    #         )
    #         return

    #     async with self.client() as client:
    #         trainer: Trainer = await client.create_trainer(**profile_data)
    #         print(trainer)
    #         user = await trainer.get_user()
    #         await user.add_discord(ctx.author)

    #         update: Update = await trainer.post(
    #             data_source="ts_registration",  # "ss_registration" is image else "ts_registration",
    #             stats=update_data,
    #             update_time=snowflake_time(ctx.interaction.id),
    #         )

    #     message = await ctx.send(chat_formatting.success(f"Profile created for {ctx.author.mention}."))
    #     embed: ProfileCard = await ProfileCard(self._common, ctx, trainer=trainer, update=update)

    #     await message.edit(embed=embed)
