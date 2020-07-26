import json
import logging
from typing import Dict

import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf


log: logging.Logger = logging.getLogger("red.tdx.settings")
_ = Translator("TrainerDex", __file__)


class QuickStart(commands.Cog):
    def __init__(self, bot: Red, config: Config) -> None:
        self.bot: Red = bot
        self.config: Config = config

    @commands.command(name="quickstart")
    async def quickstart(self, ctx: commands.Context) -> None:
        await ctx.send(_("Looking for team roles..."))

        try:
            mystic_role: discord.Role = min(
                [x for x in ctx.guild.roles if _("Mystic").casefold() in x.name.casefold()]
            )
        except ValueError:
            mystic_role = None
        if mystic_role:
            await getattr(self.config.guild(ctx.guild), "mystic_role").set(mystic_role.id)
            await ctx.send(
                _("`{key}` set to {value}").format(key="mystic_role", value=mystic_role.mention)
            )

        try:
            valor_role: discord.Role = min(
                [x for x in ctx.guild.roles if _("Valor").casefold() in x.name.casefold()]
            )
        except ValueError:
            valor_role = None
        if valor_role:
            await getattr(self.config.guild(ctx.guild), "valor_role").set(valor_role.id)
            await ctx.send(
                _("`{key}` set to {value}").format(key="valor_role", value=valor_role.mention)
            )

        try:
            instinct_role: discord.Role = min(
                [x for x in ctx.guild.roles if _("Instinct").casefold() in x.name.casefold()]
            )
        except ValueError:
            instinct_role = None
        if instinct_role:
            await getattr(self.config.guild(ctx.guild), "instinct_role").set(instinct_role.id)
            await ctx.send(
                _("`{key}` set to {value}").format(
                    key="instinct_role", value=instinct_role.mention
                )
            )

        await ctx.send(_("Looking for TL40 role..."))

        try:
            tl40_role: discord.Role = min(
                [x for x in ctx.guild.roles if _("Level 40").casefold() in x.name.casefold()]
            )
        except ValueError:
            tl40_role = None
        if tl40_role:
            await getattr(self.config.guild(ctx.guild), "tl40_role").set(tl40_role.id)
            await ctx.send(
                _("`{key}` set to {value}").format(key="tl40_role", value=tl40_role.mention)
            )

        await ctx.send(_("That's it for now."))

        settings: Dict = await self.config.guild(ctx.guild).all()
        settings: str = json.dumps(settings, indent=2, ensure_ascii=False)
        await ctx.send(cf.box(settings, "json"))
