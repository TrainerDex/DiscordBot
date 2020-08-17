import datetime
import json
import logging
from typing import Optional

import discord
from redbot.core import commands
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf

from . import converters, client
from .abc import MixinMeta
from .embeds import ProfileCard
from .utils import loading

log: logging.Logger = logging.getLogger(__name__)
_ = Translator("TrainerDex", __file__)


class Profile(MixinMeta):
    @commands.group(name="profile", case_insensitive=True)
    async def profile(self, ctx: commands.Context) -> None:
        """⬎ View, edit and create profiles. View Trainer Codes and more..."""
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
                "start_date": trainer.start_date.isoformat(),
                "faction": trainer.faction,
                "trainer_code": trainer.trainer_code,
                "is_banned": trainer.is_banned,
                "is_verified": trainer.is_verified,
                "is_visible": trainer.is_visible,
                "updates__len": len(trainer._updates),
            }
            data: str = json.dumps(data, indent=2, ensure_ascii=False)
            await ctx.send(cf.box(data, "json"))

    @profile.command(name="lookup", aliases=["whois", "find", "progress", "trainer"])
    async def profile__lookup(
        self, ctx: commands.Context, trainer: converters.TrainerConverter = None,
    ) -> None:
        """Find a profile given a username."""

        async with ctx.typing():
            message: discord.Message = await ctx.send(loading(_("Searching for profile…")))

            self_profile = False
            if trainer is None:
                trainer: client.Trainer = await converters.TrainerConverter().convert(
                    ctx, ctx.author, cli=self.client
                )
                self_profile = True

            if trainer:
                if trainer.is_visible:
                    await message.edit(content=loading(_("Found profile. Loading…")))
                elif self_profile:
                    if ctx.guild:
                        await message.edit(content=_("Sending in DMs"))
                        message = await ctx.author.send(
                            content=loading(_("Found profile. Loading…"))
                        )
                    else:
                        await message.edit(content=loading(_("Found profile. Loading…")))
                else:
                    await message.edit(content=loading(_("Profile deactivated or hidden.")))
                    return
            else:
                await message.edit(content=cf.warning(_("Profile not found.")))
                return

            embed: discord.Embed = await ProfileCard(
                ctx=ctx, bot=self.bot, client=self.client, trainer=trainer, emoji=self.emoji
            )
            await message.edit(content=loading(_("Checking progress…")), embed=embed)
            await embed.show_progress()
            await message.edit(content=loading(_("Loading leaderboards…")), embed=embed)
            await embed.add_leaderboard()
            if ctx.guild:
                await message.edit(embed=embed)
                await embed.add_guild_leaderboard(ctx.guild)
            await message.edit(content=None, embed=embed)

    @profile.group(name="edit", case_insensitive=True)
    async def profile__edit(self, ctx: commands.Context) -> None:
        """Edit various aspects about your profile"""
        pass

    @profile__edit.command(name="start_date")
    async def profile__edit__start_date(
        self, ctx: commands.Context, value: Optional[converters.DateConverter] = None
    ) -> None:
        """Set the Start Date on your profile

        This is the date you started playing Pokemon Go and is just under Total XP
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
                await trainer.edit(start_date=value)
                await ctx.tick()
                await ctx.send(
                    _("`{key}` set to {value}").format(key="trainer.start_date", value=value),
                    delete_after=30,
                )
        else:
            await ctx.send_help()
            value: datetime.date = trainer.start_date
            await ctx.send(_("`{key}` is {value}").format(key="trainer.start_date", value=value))

    @profile__edit.command(name="visible")
    async def profile__edit__visible(
        self, ctx: commands.Context, value: Optional[bool] = None
    ) -> None:
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
