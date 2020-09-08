import logging
import os
import math
from typing import Final, Optional, Union

import discord
import humanize
from redbot.core import commands
from redbot.core.commands.converter import Literal
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf
from redbot.vendored.discord.ext import menus

import trainerdex as client
from . import converters
from .abc import MixinMeta
from .embeds import BaseCard
from .utils import append_icon, loading

log: logging.Logger = logging.getLogger(__name__)
POGOOCR_TOKEN_PATH: Final = os.path.join(os.path.dirname(__file__), "data/key.json")
_ = Translator("TrainerDex", __file__)


class LeaderboardPages(menus.AsyncIteratorPageSource):
    def __init__(self, *args, **kwargs):
        self.base = kwargs.pop("base")
        self.emoji = kwargs.pop("emoji")
        self.stat = kwargs.pop("stat")
        super().__init__(*args, **kwargs)

    async def format_page(self, menu, page):
        emb: discord.Embed = self.base.copy()
        for entry in page:
            emb.add_field(
                name="{pos} {handle} {faction}".format(
                    pos=append_icon(self.emoji.get("number", "#"), entry.position),
                    handle=entry.username,
                    faction=self.emoji.get(entry.faction.verbose_name.lower()),
                ),
                value="{value} • TL{level} • {dt}".format(
                    value=append_icon(
                        self.emoji.get(self.stat[0]), cf.humanize_number(entry.total_xp)
                    ),
                    level=entry.level,
                    dt=humanize.naturaldate(entry.last_updated),
                ),
                inline=False,
            )
        emb.set_footer(
            text=_("Page {page} of {pages} | {footer}").format(
                page=menu.current_page + 1,
                pages=math.ceil(len(menu.source.iterator) / menu.source.per_page),
                footer=emb.footer.text,
            ),
            icon_url=emb.footer.icon_url,
        )
        return {"embed": emb, "content": None}


class Leaderboard(MixinMeta):
    leaderboard_aliases = []
    leaderboard_aliases.extend(["bestenliste", "bl"])  # de-DE German
    leaderboard_aliases.extend(["clasificación"])  # es-ES Spanish
    leaderboard_aliases.extend(["lb", "LB"])  # en-US English
    leaderboard_aliases.extend(["classement"])  # fr-FR French
    leaderboard_aliases.extend(["classifica"])  # it-IT Italian
    leaderboard_aliases.extend(["リーダーボード"])  # ja-JP Japanese
    leaderboard_aliases.extend(["리더보드"])  # ko-KR Korean
    leaderboard_aliases.extend(["entre-os-melhores", "melhores", "eos"])  # pt-BR Portuguese
    leaderboard_aliases.extend(["ลีดเดอร์บอร์ด"])  # th-TH Thai
    leaderboard_aliases.extend(["排行榜"])  # zh-HK Chinese (Traditional)

    @commands.command(name="leaderboard", aliases=list(set(leaderboard_aliases)))
    async def leaderboard(
        self,
        ctx: commands.Context,
        leaderboard: Optional[Literal["global", "guild", "server"]] = "guild",
        *filters: Union[converters.TeamConverter, converters.LevelConverter],
    ) -> None:
        """Leaderboards

        Parameters:
            `leaderboard`: str
                options are `guild` (or `server`) and `global`
            `filters`: Union[Team, Level]
                If you mention any team, it'll filter to that. You can mention more than one team.
                If you mention one level, it'll show that level and all below.
                If you mention more than one level, it will show all between the lowest and highest level you mention.

        Example:
            `[p]leaderboard`
            Shows the server leaderboard, unless you're in DMs.

            `[p]leaderboard global`
            Shows the global leaderboard

            `[p]leaderboard valor mystic 24`
            Shows the server leaderboard, post-filtered to only show valor and mystic players under or equal to level 24

            `[p]leaderboard 15 24`
            Shows the server leaderboard, post-filtered to only show players between level 15 and 24 (inclusive)
        """

        leaderboard = leaderboard if ctx.guild else "global"
        stat = ("total_xp", _("Total XP"))
        factions = (
            {x for x in filters if isinstance(x, client.Faction)}
            if [x for x in filters if isinstance(x, client.Faction)]
            else {client.Faction(i) for i in range(0, 4)}
        )
        levels = {x.level for x in filters if isinstance(x, client.Level)}
        if len(levels) > 1:
            levels = range(
                min(levels),
                max(levels) + 1,
            )
        elif len(levels) == 1:
            levels = range(levels.pop() + 1)
        else:
            levels = range(1, 41)

        levels = {client.update.get_level(level=i) for i in levels}

        leaderboard_title = append_icon(
            icon=self.emoji.get(stat[0], ""),
            text=_("{stat} Leaderboard").format(stat=stat[1]),
        )

        emb = await BaseCard(ctx, title=leaderboard_title)
        if leaderboard in ("guild", "server"):
            emb.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

        await ctx.tick()

        message = await ctx.send(
            loading(_("{tag} Downloading {leaderboard}…")).format(
                tag=ctx.author.mention, leaderboard=leaderboard_title
            )
        )
        leaderboard = await self.client.get_leaderboard(
            guild=ctx.guild if leaderboard in ("guild", "server") else None
        )

        await message.edit(
            content=loading(_("{tag} Filtering {leaderboard}…")).format(
                tag=ctx.author.mention, leaderboard=leaderboard_title
            )
        )
        leaderboard.filter(lambda x: x.faction in factions).filter(lambda x: x.level in levels)

        if len(leaderboard) < 1:
            await message.edit(content=_("No results to display!"))
        else:
            embeds = LeaderboardPages(
                leaderboard, per_page=10, base=emb, emoji=self.emoji, stat=stat
            )
            menu = menus.MenuPages(
                source=embeds, timeout=300.0, message=message, clear_reactions_after=True
            )
            await menu.show_page(0)
            await menu.start(ctx)
