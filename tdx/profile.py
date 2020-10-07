import contextlib
import datetime
import json
import logging
import os
from typing import Final, Optional, Union

import discord
from redbot.core import commands
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf

import trainerdex as client
import PogoOCR
from . import converters
from .abc import MixinMeta
from .embeds import ProfileCard
from .utils import loading

log: logging.Logger = logging.getLogger(__name__)
_ = Translator("TrainerDex", __file__)
POGOOCR_TOKEN_PATH: Final = os.path.join(os.path.dirname(__file__), "data/key.json")


class Profile(MixinMeta):
    @commands.command(name="profile", aliases=["trainer", "progress", "trnr", "whois"])
    async def view_profile(
        self,
        ctx: commands.Context,
        trainer: Optional[converters.TrainerConverter] = None,
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

            embed: ProfileCard = await ProfileCard(
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
        self, ctx: commands.Context, value: Optional[converters.DateConverter] = None
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
    async def set_friendcode(self, ctx: commands.Context, value: str) -> None:
        async with ctx.typing():
            try:
                trainer = await converters.TrainerConverter().convert(
                    ctx, ctx.author, cli=self.client
                )
            except commands.BadArgument:
                await ctx.send(cf.error("No profile found."))

        if value is not None:
            async with ctx.typing():
                await trainer.edit(trainer_code=value)
                await ctx.tick()
                await ctx.send(
                    _("{trainer.nickname}'s Trainer Code set to {trainer.trainer_code}").format(
                        trainer=trainer
                    )
                )

    @edit_profile.command(name="team", aliases=["faction"])
    async def edit_profile__team(self, ctx: commands.Context) -> None:
        """Edit your team."""
        # Check if image attached, if not, ask for one
        async with ctx.typing():
            if len(ctx.message.attachments) == 1:
                img_url = ctx.message.attachments[0].proxy_url
            else:
                await ctx.send(
                    _(
                        "Please attach an image of your Trainer profile, clearly showing your username and team colours."
                    )
                )
                img_url = (
                    (
                        await self.bot.wait_for(
                            "message",
                            check=(
                                lambda message: (message.author == ctx.author)
                                and (message.channel == ctx.channel)
                                and (len(message.attachments) == 1)
                            ),
                        )
                    )
                    .attachments[0]
                    .proxy_url
                )

        async with ctx.typing():
            try:
                trainer = await converters.TrainerConverter().convert(ctx, ctx.author, self.client)
            except commands.BadArgument:
                await ctx.send(cf.error("No profile found."))
                return

        async with ctx.typing():
            # Extract team from image
            ocr = PogoOCR.ProfileSelf(POGOOCR_TOKEN_PATH, image_uri=img_url)
            ocr.get_text()
            team: client.Faction = client.Faction(ocr.team)

            if not self.match_usernames(trainer.nickname, ocr.username):
                await ctx.send(
                    "Nickname doesn't match. (Stored nickname: `{}`. Detected: `{}`)".format(
                        trainer.nickname, ocr.username
                    )
                )
                return

            await ctx.send("Team detected: `{}`".format(team))

            old_team = trainer.team

            if old_team != team:
                await trainer.edit(faction=team)
                embed = await ProfileCard(
                    ctx=ctx, client=self.client, trainer=trainer, emoji=self.emoji
                )
                await ctx.send(
                    content=_("Team successfully updated on the database."), embed=embed
                )

            # Ensure team roles are set correctly on discord
            await self.change_team_roles(
                ctx.guild,
                ctx.author,
                old_team,
                team,
                reason=_(
                    "User changed their team with `[p]editprofile team` and supplying a screenshot"
                ),
            )

            # Ask users permission to change on other Discords

            # TODO: Add system for restricting guilds to certain teams, kick users from guild if team is bad
