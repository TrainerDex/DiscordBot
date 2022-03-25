import datetime
import re
from calendar import month_name
from typing import Optional

from aiohttp import ClientResponseError
from discord import OptionChoice, user_command
from discord.commands import ApplicationContext, Option, slash_command
from discord.user import User
from discord.webhook import WebhookMessage

from trainerdex_discord_bot.cogs.interface import Cog
from trainerdex_discord_bot.embeds import ProfileCard
from trainerdex_discord_bot.utils import chat_formatting
from trainerdex_discord_bot.utils.converters import get_trainer, get_trainer_from_user


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
        await ctx.defer()

        if username or user:
            trainer = await get_trainer(self.client, nickname=username, user=user)
        else:
            trainer = await get_trainer_from_user(self.client, ctx.interaction.user)

        if trainer is None or not trainer.is_visible:
            await ctx.followup.send(chat_formatting.error("No profile found."), ephemeral=True)
            return

        embed: ProfileCard = await ProfileCard(self._common, ctx, trainer=trainer)
        response: WebhookMessage = await ctx.followup.send(
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
        await ctx.defer()

        trainer = await get_trainer_from_user(self.client, user)

        if trainer is None or not trainer.is_visible:
            await ctx.followup.send(chat_formatting.error("No profile found."), ephemeral=True)
            return

        embed: ProfileCard = await ProfileCard(self._common, ctx, trainer=trainer)
        response: WebhookMessage = await ctx.followup.send(
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
        await ctx.defer()

        if username or user:
            trainer = await get_trainer(self.client, nickname=username, user=user)
        else:
            trainer = await get_trainer_from_user(self.client, ctx.interaction.user)

        if trainer is None or not trainer.is_visible:
            await ctx.followup.send(chat_formatting.error("No profile found."), ephemeral=True)
            return
        elif not trainer.trainer_code:
            await ctx.followup.send(
                chat_formatting.warning(f"{trainer.nickname} has not set their Trainer Code.")
            )
        else:
            await ctx.followup.send(chat_formatting.info(f"{trainer.nickname}'s Trainer Code is:"))
            await ctx.followup.send(chat_formatting.inline(trainer.trainer_code))

    # edit_profile = bot.create_group(
    #     name="edit-profile", description="Edit various aspects about your profile."
    # )

    @slash_command(
        name="edit-start-date",
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
    async def slash__edit_start_date(
        self,
        ctx: ApplicationContext,
        year: int,
        month: int,
        day: int,
    ) -> None:
        """Set the Start Date on your profile

        This is the date you started playing Pokémon Go and is just under Total XP
        """
        await ctx.defer()

        try:
            start_date = datetime.date(year, month, day)
        except ValueError as e:
            await ctx.followup.send(chat_formatting.error(str(e)))
            return

        if start_date < datetime.date(2016, 7, 5):
            await ctx.followup.send(chat_formatting.error("Start Date must be after 2016-07-05"))
            return

        if start_date > datetime.date.today():
            await ctx.followup.send(chat_formatting.error("Start Date must not be in the future"))
            return

        trainer = await get_trainer_from_user(self.client, ctx.interaction.user)

        if trainer is None:
            await ctx.followup.send(chat_formatting.error("No profile found."), ephemeral=True)
            return

        try:
            await trainer.edit(start_date=start_date)
        except ClientResponseError:
            self.logger.exception(f"Unable to set {trainer.nickname}'s start date to {start_date}")
            await ctx.followup.send(
                chat_formatting.error("Unable to set start date due to an unknown error.")
            )
        else:
            await ctx.followup.send(
                chat_formatting.success(f"{trainer.nickname}'s start date set to {start_date}.")
            )

    # @command(name="visible", aliases=["gdpr"])
    # async def toggle_gdpr(self, ctx: commands.Context, value: Optional[bool] = None) -> None:
    #     """Set if you should appear in Leaderboards

    #     Hide or show yourself on leaderboards at will!
    #     """
    #     async with ctx.typing():
    #         trainer = await get_trainer_from_user(self.client, ctx.interaction.user)

    #         if trainer is None:
    #             await ctx.followup.send(chat_formatting.error("No profile found."), ephemeral=True)
    #             return

    #     if value is not None:
    #         async with ctx.typing():
    #             await trainer.edit(is_visible=value)
    #             await ctx.message.add_reaction("✅")
    #             await ctx.send(
    #                 "`{key}` set to {value}".format(key="trainer.is_visible", value=value),
    #                 delete_after=30,
    #             )
    #     else:
    #         await ctx.send_help()
    #         value: datetime.date = trainer.is_visible
    #         await ctx.send("`{key}` is {value}".format(key="trainer.is_visible", value=value))

    @slash_command(name="set-trainer-code")
    async def set_trainer_code(self, ctx: ApplicationContext, code: str) -> None:
        await ctx.defer()

        trainer = await get_trainer_from_user(self.client, ctx.interaction.user)

        if trainer is None:
            await ctx.followup.send(chat_formatting.error("No profile found."), ephemeral=True)
            return

        if not re.match(r"(\d{4}\s?){3}", code):
            await ctx.followup.send(chat_formatting.error("Invalid Trainer Code."))
        else:
            await trainer.edit(trainer_code=code.replace(" ", ""))
            await ctx.followup.send(
                f"Your Trainer Code was successfully set to {trainer.trainer_code}",
                empemberal=True,
            )
