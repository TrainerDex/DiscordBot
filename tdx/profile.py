import datetime
import json
import logging
import re
from typing import Optional

import discord
from redbot.core import commands
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf
from trainerdex.trainer import Trainer

from . import converters
from .abc import MixinMeta
from .embeds import ProfileCard
from .utils import loading

logger: logging.Logger = logging.getLogger(__name__)
_ = Translator("TrainerDex", __file__)


class Profile(MixinMeta):
    @commands.command(name="profile", aliases=["trainer", "progress", "trnr", "whois"])
    async def view_profile(
        self,
        ctx: commands.Context,
        nickname: str = None,
    ) -> None:
        """Find a profile given a username."""

        async with ctx.typing():
            try:
                logger.debug("searching for trainer by discord uid: %s", ctx.author.id)
                author_profile = await converters.TrainerConverter().convert(
                    ctx, ctx.author, cli=self.client
                )
            except commands.BadArgument:
                author_profile = None

            message: discord.Message = await ctx.send(loading(_("Searching for profile…")))

            if nickname is None:
                trainer = author_profile
            else:
                try:
                    logger.debug("searching for trainer by username: %s", nickname)
                    trainer: Trainer = await converters.TrainerConverter().convert(
                        ctx, nickname, cli=self.client
                    )
                except commands.BadArgument:
                    await message.edit(content=cf.warning(_("Profile not found.")))
                    return

            if trainer:
                if trainer.is_visible:
                    await message.edit(content=loading(_("Found profile. Loading…")))
                elif trainer == author_profile:
                    if ctx.guild:
                        await message.edit(content=_("Sending in DMs"))
                        message = await ctx.author.send(
                            content=loading(_("Found profile. Loading…"))
                        )
                    else:
                        await message.edit(content=loading(_("Found profile. Loading…")))
                else:
                    await message.edit(content=cf.warning(_("Profile deactivated or hidden.")))
                    return
            else:
                await message.edit(content=cf.warning(_("Profile not found.")))
                return

            embed: discord.Embed = await ProfileCard(
                ctx=ctx, client=self.client, trainer=trainer, emoji=self.emoji
            )
            await message.edit(content=loading(_("Checking progress…")), embed=embed)
            await embed.show_progress()
            await message.edit(content=loading(_("Loading leaderboards…")), embed=embed)
            await embed.add_leaderboard()
            if ctx.guild:
                await message.edit(embed=embed)
                await embed.add_guild_leaderboard(ctx.guild)
            await message.edit(content=None, embed=embed)

    @commands.command(name="trainercode", aliases=["friendcode", "trainer-code", "friend-code"])
    async def get_trainer_code(
        self,
        ctx: commands.Context,
        nickname: str = None,
    ) -> None:
        """Find a profile given a username."""

        async with ctx.typing():
            try:
                logger.debug("searching for trainer by discord uid: %s", ctx.author.id)
                author_profile = await converters.TrainerConverter().convert(
                    ctx, ctx.author, cli=self.client
                )
            except commands.BadArgument:
                author_profile = None

            message: discord.Message = await ctx.send(loading(_("Searching for profile…")))

            if nickname is None:
                trainer = author_profile
            else:
                try:
                    logger.debug("searching for trainer by username: %s", nickname)
                    trainer: Trainer = await converters.TrainerConverter().convert(
                        ctx, nickname, cli=self.client
                    )
                except commands.BadArgument:
                    await message.edit(content=cf.warning(_("Profile not found.")))
                    return

            if trainer:
                if trainer.is_visible and trainer.trainer_code:
                    await message.edit(content=trainer.trainer_code)
                elif trainer.is_visible and not trainer.trainer_code:
                    await message.edit(content=cf.warning(_("Unknown.")))
                else:
                    await message.edit(
                        content=cf.warningloading(_("Profile deactivated or hidden."))
                    )
            else:
                await message.edit(content=cf.warning(_("Profile not found.")))

    @commands.group(name="editprofile", case_insensitive=True)
    async def edit_profile(self, ctx: commands.Context) -> None:
        """Edit various aspects about your profile"""
        if ctx.invoked_subcommand is None:
            async with ctx.typing():
                try:
                    trainer = await converters.TrainerConverter().convert(
                        ctx, ctx.author, cli=self.client
                    )
                except commands.BadArgument:
                    await ctx.send(cf.error("No profile found."))
                    return

            data = {
                "nickname": trainer.nickname,
                "start_date": trainer.start_date.isoformat() if trainer.start_date else None,
                "faction": trainer.faction,
                "trainer_code": trainer.trainer_code,
                "is_banned": trainer.is_banned,
                "is_verified": trainer.is_verified,
                "is_visible": trainer.is_visible,
                "updates__len": len(trainer._updates),
            }
            data: str = json.dumps(data, indent=2, ensure_ascii=False)
            await ctx.send(cf.box(data, "json"))

    @edit_profile.command(name="startdate")
    async def edit_start_date(
        self,
        ctx: commands.Context,
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None,
    ) -> None:
        """Set the Start Date on your profile

        This is the date you started playing Pokémon Go and is just under Total XP
        """
        async with ctx.typing():
            try:
                trainer = await converters.TrainerConverter().convert(
                    ctx, ctx.author, cli=self.client
                )
            except commands.BadArgument:
                await ctx.send(cf.error("No profile found."))

        if year and month and day:
            try:
                start_date = datetime.date(year, month, day)
            except ValueError as e:
                await ctx.send(
                    _("Can't set `{key}` because {error}").format(
                        key="trainer.start_date", error=e
                    )
                )
                return

            async with ctx.typing():
                if start_date < datetime.date(2016, 7, 5):
                    await ctx.send(
                        _("Can't set `{key}` because the date is too early").format(
                            key="trainer.start_date"
                        )
                    )
                    return

                await trainer.edit(start_date=start_date)
                await ctx.tick()
                await ctx.send(
                    _("`{key}` set to {value}").format(key="trainer.start_date", value=start_date),
                    delete_after=30,
                )
        else:
            await ctx.send_help()
            value: datetime.date = trainer.start_date
            await ctx.send(_("`{key}` is {value}").format(key="trainer.start_date", value=value))

    @edit_profile.command(name="visible", aliases=["gdpr"])
    async def toggle_gdpr(self, ctx: commands.Context, value: Optional[bool] = None) -> None:
        """Set if you should appear in Leaderboards

        Hide or show yourself on leaderboards at will!
        """
        async with ctx.typing():
            try:
                trainer = await converters.TrainerConverter().convert(
                    ctx, ctx.author, cli=self.client
                )
            except commands.BadArgument:
                await ctx.send(cf.error("No profile found."))

        if value is not None:
            async with ctx.typing():
                await trainer.edit(is_visible=value)
                await ctx.tick()
                await ctx.send(
                    _("`{key}` set to {value}").format(key="trainer.is_visible", value=value),
                    delete_after=30,
                )
        else:
            await ctx.send_help()
            value: datetime.date = trainer.is_visible
            await ctx.send(_("`{key}` is {value}").format(key="trainer.is_visible", value=value))

    @edit_profile.command(
        name="trainercode", aliases=["friendcode", "trainer-code", "friend-code"]
    )
    async def set_trainer_code(
        self, ctx: commands.Context, *, value: converters.TrainerCodeValidator
    ) -> None:
        return await self._set_trainer_code(ctx, False, value)

    async def _set_trainer_code(
        self,
        ctx: commands.Context,
        no_error: bool,
        value: converters.TrainerCodeValidator,
    ) -> None:
        async with ctx.typing():
            try:
                trainer = await converters.TrainerConverter().convert(
                    ctx, ctx.author, cli=self.client
                )
            except commands.BadArgument:
                if no_error:
                    return
                await ctx.send(cf.error("No profile found."))

        if value:
            async with ctx.typing():
                await trainer.edit(trainer_code=value)
                await ctx.tick()
                await ctx.send(
                    _("{trainer.nickname}'s Trainer Code set to {trainer.trainer_code}").format(
                        trainer=trainer
                    )
                )

    @commands.Cog.listener("on_message_without_command")
    async def pokenav_set_trainer_code(self, message: discord.Message) -> None:
        ctx = await self.bot.get_context(message)
        del message
        if not (await self.bot.message_eligible_as_command(ctx.message)):
            return

        if await self.bot.cog_disabled_in_guild(self, ctx.guild):
            return

        match = re.match(r"^\$(?:stc|set-trainer-code)\s(.*)$", ctx.message.content)
        if match:
            return await self._set_trainer_code(ctx, True, match[1])
