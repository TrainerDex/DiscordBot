import datetime
import json
import logging
from typing import Optional

import discord
from redbot.core import commands
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf

import trainerdex as client
from . import converters
from .abc import MixinMeta
from .embeds import ProfileCard
from .utils import loading

log: logging.Logger = logging.getLogger(__name__)
_ = Translator("TrainerDex", __file__)


class Profile(MixinMeta):
    profile_aliases = []
    profile_aliases.extend(["profil"])  # de-DE German
    profile_aliases.extend(["perfil"])  # es-ES Spanish
    profile_aliases.extend([])  # en-US English
    profile_aliases.extend(["profil"])  # fr-FR French
    profile_aliases.extend(["profilo"])  # it-IT Italian
    profile_aliases.extend(["プロフィール"])  # ja-JP Japanese
    profile_aliases.extend(["프로필"])  # ko-KR Korean
    profile_aliases.extend(["perfil"])  # pt-BR Portuguese
    profile_aliases.extend(["ข้อมูลส่วนตัว"])  # th-TH Thai
    profile_aliases.extend(["個人資料"])  # zh-HK Chinese (Traditional)

    @commands.group(name="profile", case_insensitive=True, aliases=list(set(profile_aliases)))
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

    profile__lookup_aliases = []
    profile__lookup_aliases.extend(["sieh-nach-oben", "finden", "wer-ist"])  # de-DE German
    profile__lookup_aliases.extend(["buscar", "hallar", "quien-es"])  # es-ES Spanish
    profile__lookup_aliases.extend(["find", "whois"])  # en-US English
    profile__lookup_aliases.extend(["chercher", "découvrir", "qui-est"])  # fr-FR French
    profile__lookup_aliases.extend(["consultare", "trova", "chi-è"])  # it-IT Italian
    profile__lookup_aliases.extend(["調べる", "誰が"])  # ja-JP Japanese
    profile__lookup_aliases.extend(["조회", "누구인가", "입수하다"])  # ko-KR Korean
    profile__lookup_aliases.extend(["olho-para-cima", "quem-é", "encontrar"])  # pt-BR Portuguese
    profile__lookup_aliases.extend(["ค้นหา", "ไคร", "พบ"])  # th-TH Thai
    profile__lookup_aliases.extend(["抬頭", "誰是", "藪"])  # zh-HK Chinese (Traditional)

    @profile.command(name="lookup", aliases=list(set(profile__lookup_aliases)))
    async def profile__lookup(
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

    profile__edit_aliases = []
    profile__edit_aliases.extend(["ändern"])  # de-DE German
    profile__edit_aliases.extend(["modificar"])  # es-ES Spanish
    profile__edit_aliases.extend(["modify"])  # en-US English
    profile__edit_aliases.extend(["modifier"])  # fr-FR French
    profile__edit_aliases.extend(["modificare"])  # it-IT Italian
    profile__edit_aliases.extend(["修正", "モディファイ"])  # ja-JP Japanese
    profile__edit_aliases.extend(["수정"])  # ko-KR Korean
    profile__edit_aliases.extend(["modificar"])  # pt-BR Portuguese
    profile__edit_aliases.extend(["ปรับเปลี่ยน"])  # th-TH Thai
    profile__edit_aliases.extend(["修改"])  # zh-HK Chinese (Traditional)

    @profile.group(name="edit", case_insensitive=True, aliases=list(set(profile__edit_aliases)))
    async def profile__edit(self, ctx: commands.Context) -> None:
        """Edit various aspects about your profile"""
        pass

    profile__edit__start_date_aliases = []
    profile__edit__start_date_aliases.extend(["startdatum"])  # de-DE German
    profile__edit__start_date_aliases.extend(["fecha-de-inicio", "inicio"])  # es-ES Spanish
    profile__edit__start_date_aliases.extend(["start"])  # en-US English
    profile__edit__start_date_aliases.extend(["date-de-début", "début"])  # fr-FR French
    profile__edit__start_date_aliases.extend(["data-di-inizio", "inizio"])  # it-IT Italian
    profile__edit__start_date_aliases.extend(["始めた日"])  # ja-JP Japanese
    profile__edit__start_date_aliases.extend(["시작한", "시작한-날"])  # ko-KR Korean
    profile__edit__start_date_aliases.extend(["data-de-início", "início"])  # pt-BR Portuguese
    profile__edit__start_date_aliases.extend(["วันที่เริ่มเล่น"])  # th-TH Thai
    profile__edit__start_date_aliases.extend(["開始日"])  # zh-HK Chinese (Traditional)

    @profile__edit.command(name="start_date", aliases=list(set(profile__edit__start_date_aliases)))
    async def profile__edit__start_date(
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

    profile__edit__visible_aliases = []
    profile__edit__visible_aliases.extend(["sichtbar"])  # de-DE German
    profile__edit__visible_aliases.extend([])  # es-ES Spanish
    profile__edit__visible_aliases.extend([])  # en-US English
    profile__edit__visible_aliases.extend([])  # fr-FR French
    profile__edit__visible_aliases.extend(["visibile"])  # it-IT Italian
    profile__edit__visible_aliases.extend(["見える"])  # ja-JP Japanese
    profile__edit__visible_aliases.extend(["명백한"])  # ko-KR Korean
    profile__edit__visible_aliases.extend(["visível"])  # pt-BR Portuguese
    profile__edit__visible_aliases.extend(["มองเห็นได้"])  # th-TH Thai
    profile__edit__visible_aliases.extend(["可見"])  # zh-HK Chinese (Traditional)

    @profile__edit.command(name="visible", aliases=list(set(profile__edit__visible_aliases)))
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
