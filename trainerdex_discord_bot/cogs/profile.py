import datetime
import re
from calendar import month_name
from typing import Optional

from aiohttp import ClientResponseError
from discord import Message, OptionChoice, SlashCommandGroup, user_command
from discord.commands import ApplicationContext, Option, slash_command
from discord.user import User

from trainerdex.exceptions import Forbidden, HTTPException, NotFound

from trainerdex_discord_bot.cogs.interface import Cog
from trainerdex_discord_bot.embeds import ProfileCard
from trainerdex_discord_bot.utils import chat_formatting
from trainerdex_discord_bot.utils.converters import get_trainer, get_trainer_from_user
from trainerdex_discord_bot.utils.general import send


class ProfileCog(Cog):
    @slash_command(
        name="profile",
        options=[
            Option(str, name="username", required=False),
            Option(User, name="user", required=False),
        ],
    )
    async def slash__profile(
        self,
        ctx: ApplicationContext,
        username: Optional[str] = None,
        user: Optional[User] = None,
    ) -> None:
        """Find a profile given a username or user mention."""
        if username or user:
            trainer = await get_trainer(self.client, nickname=username, user=user)
        else:
            trainer = await get_trainer_from_user(self.client, ctx.interaction.user)

        if trainer is None or not trainer.is_visible:
            await send(ctx, chat_formatting.error("No profile found."), ephemeral=True)
            return

        embed: ProfileCard = await ProfileCard(self._common, ctx, trainer=trainer)
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

    @user_command(name="View Profile")
    async def user__profile(
        self,
        ctx: ApplicationContext,
        user: User,
    ) -> None:
        trainer = await get_trainer_from_user(self.client, user)

        if trainer is None or not trainer.is_visible:
            await send(ctx, chat_formatting.error("No profile found."), ephemeral=True)
            return

        embed: ProfileCard = await ProfileCard(self._common, ctx, trainer=trainer)
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
        name="get-trainer-code",
        options=[
            Option(str, name="username", required=False),
            Option(User, name="user", required=False),
        ],
    )
    async def slash__get_trainer_code(
        self,
        ctx: ApplicationContext,
        username: Optional[str] = None,
        user: Optional[User] = None,
    ) -> None:
        """Find a profile given a username."""
        if username or user:
            trainer = await get_trainer(self.client, nickname=username, user=user)
        else:
            trainer = await get_trainer_from_user(self.client, ctx.interaction.user)

        if trainer is None or not trainer.is_visible:
            await send(ctx, chat_formatting.error("No profile found."), ephemeral=True)
            return
        elif not trainer.trainer_code:
            await send(
                ctx, chat_formatting.warning(f"{trainer.nickname} has not set their Trainer Code.")
            )
        else:
            await send(ctx, chat_formatting.info(f"{trainer.nickname}'s Trainer Code is:"))
            await send(ctx, chat_formatting.inline(trainer.trainer_code))

    edit_profile = SlashCommandGroup("edit-profile", "Edit various aspects about your profile.")

    @edit_profile.command(
        name="start-date",
        options=[
            Option(
                int,
                name="year",
                required=True,
                min_value=2016,
                max_value=(datetime.date.today() + datetime.timedelta(days=1)).year,
                choices=[
                    OptionChoice(name=str(year), value=year)
                    for year in range(
                        2016,
                        (datetime.date.today() + datetime.timedelta(days=1)).year + 1,
                    )
                ],
            ),
            Option(
                int,
                name="month",
                required=True,
                min_value=1,
                max_value=12,
                choices=[
                    OptionChoice(name=month_name[month], value=month)
                    for month in range(
                        1,
                        13,
                    )
                ],
            ),
            Option(
                int,
                name="day",
                required=True,
                min_value=1,
                max_value=31,
                autocomplete=True,
            ),
        ],
    )
    async def set_start_date(
        self,
        ctx: ApplicationContext,
        year: int,
        month: int,
        day: int,
    ) -> None:
        """Set the Start Date on your profile

        This is the date you started playing Pokémon Go and is just under Total XP
        """
        try:
            start_date = datetime.date(year, month, day)
        except ValueError as e:
            await send(ctx, chat_formatting.error(str(e)))
            return

        if start_date < datetime.date(2016, 7, 5):
            await send(ctx, chat_formatting.error("Start Date must be after 2016-07-05"))
            return

        if start_date > datetime.date.today():
            await send(ctx, chat_formatting.error("Start Date must not be in the future"))
            return

        trainer = await get_trainer_from_user(self.client, ctx.interaction.user)

        if trainer is None:
            await send(ctx, chat_formatting.error("No profile found."), ephemeral=True)
            return

        try:
            await trainer.edit(start_date=start_date)
        except ClientResponseError:
            self.logger.exception(f"Unable to set {trainer.nickname}'s start date to {start_date}")
            await send(
                ctx, chat_formatting.error("Unable to set start date due to an unknown error.")
            )
        else:
            await send(
                ctx,
                chat_formatting.success(f"{trainer.nickname}'s start date set to {start_date}."),
            )

    @edit_profile.command(name="visible", options=[Option(bool, name="visible", required=True)])
    async def set_profile_visible(self, ctx: ApplicationContext, visible: bool) -> None:
        """Set if you should appear in Leaderboards

        Hide or show yourself on leaderboards at will!
        """
        trainer = await get_trainer_from_user(self.client, ctx.interaction.user)

        if trainer is None:
            await send(
                ctx,
                chat_formatting.error("No profile found."),
                ephemeral=True,
            )
            return

        try:
            await trainer.edit(is_visible=visible)
        except (Forbidden, NotFound, HTTPException) as e:
            await send(
                ctx,
                chat_formatting.error("Unable to set visibility due to an unknown error."),
                ephemeral=True,
            )
            self.logger.exception(f"Unable to set {trainer.nickname}'s visibility to {visible}", e)

        if trainer.is_visible:
            await send(
                ctx,
                chat_formatting.success("Your profile is visible to others."),
                ephemeral=True,
            )
        else:
            await send(
                ctx,
                chat_formatting.success("Your profile is hidden from others."),
                ephemeral=True,
            )

    @edit_profile.command(name="trainer-code")
    async def set_trainer_code(self, ctx: ApplicationContext, code: str) -> None:
        trainer = await get_trainer_from_user(self.client, ctx.interaction.user)

        if trainer is None:
            await send(ctx, chat_formatting.error("No profile found."), ephemeral=True)
            return

        if not re.match(r"(\d{4}\s?){3}", code):
            await send(ctx, chat_formatting.error("Invalid Trainer Code."))
        else:
            await trainer.edit(trainer_code=code.replace(" ", ""))
            await send(
                ctx,
                f"Your Trainer Code was successfully set to {trainer.trainer_code}",
                empemberal=True,
            )
