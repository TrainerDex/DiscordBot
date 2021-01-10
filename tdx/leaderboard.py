import logging
import math
import os
from typing import Final, Optional, Union

import discord
import humanize
from redbot.core import commands
from redbot.core.commands.converter import Literal
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf
from redbot.vendored.discord.ext import menus
from trainerdex.faction import Faction
from trainerdex.update import Level, get_level

from . import converters
from .abc import MixinMeta
from .embeds import BaseCard
from .utils import append_icon, loading

logger: logging.Logger = logging.getLogger(__name__)
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
                    value=append_icon(self.emoji.get(self.stat), cf.humanize_number(entry.value)),
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
        return {"embed": emb}


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
        stat: Optional[
            Literal["travel_km", "capture_total", "pokestops_visited", "total_xp"]
        ] = "total_xp",
        *filters: Union[converters.TeamConverter, converters.LevelConverter],
    ) -> None:
        """Leaderboards

        Parameters:
            `leaderboard`: text
                options are `guild` (or `server`) and `global`
            `stat`: text
                options are `travel_km`, `capture_total`, `pokestops_visited`, `total_xp`
            `filters`: Union[Team, Level]
                If you mention any team, it'll filter to that. You can mention more than one team.
                If you mention one level, it'll show that level and all below.
                If you mention more than one level, it will show all between the lowest and highest level you mention.

        Example:
            `[p]leaderboard`
            Shows the server leaderboard, unless you're in DMs.

            `[p]leaderboard global`
            Shows the global leaderboard, limited to the top 1000

            `[p]leaderboard valor mystic 24`
            Shows the server leaderboard, post-filtered to only show valor and mystic players under or equal to level 24

            `[p]leaderboard 15 24`
            Shows the server leaderboard, post-filtered to only show players between level 15 and 24 (inclusive)
        """

        leaderboard = leaderboard if ctx.guild else "global"
        is_guild = True if leaderboard == "guild" else False

        # Convert stat_name for API
        stat = {
            "travel_km": "badge_travel_km",
            "capture_total": "badge_capture_total",
            "pokestops_visited": "badge_pokestops_visited",
            "total_xp": "total_xp",
        }[stat]

        stat_name = {
            "badge_travel_km": _("Distance Walked"),
            "badge_capture_total": _("Pokémon Caught"),
            "badge_pokestops_visited": _("PokéStops Visited"),
            "total_xp": _("Total XP"),
        }

        factions = (
            {x for x in filters if isinstance(x, Faction)}
            if [x for x in filters if isinstance(x, Faction)]
            else {Faction(i) for i in range(0, 4)}
        )
        levels = {x.level for x in filters if isinstance(x, Level)}
        if len(levels) > 1:
            levels = range(
                min(levels),
                max(levels) + 1,
            )
        elif len(levels) == 1:
            levels = range(levels.pop() + 1)
        else:
            levels = range(1, 51)

        levels = {get_level(level=i) for i in levels}

        leaderboard_title = append_icon(
            icon=self.emoji.get(stat, ""),
            text=_("{stat} Leaderboard").format(stat=stat_name.get(stat, stat)),
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
            stat=stat, guild=ctx.guild if leaderboard in ("guild", "server") else None
        )
        if is_guild:
            emb.description = _(
                """Average {stat_name}: {stat_avg}
                Trainers: {stat_count}
                Sum of all Trainers: {stat_sum}"""
            ).format(
                stat_name=stat_name.get(stat, stat),
                stat_avg=cf.humanize_number(leaderboard.avg),
                stat_count=cf.humanize_number(leaderboard.count),
                stat_sum=cf.humanize_number(leaderboard.sum),
            )

        await message.edit(
            content=loading(_("{tag} Filtering {leaderboard}…")).format(
                tag=ctx.author.mention, leaderboard=leaderboard_title
            )
        )
        leaderboard.filter(lambda x: x.faction in factions).filter(
            lambda x: get_level(level=int(str(x.level).split("-")[0])) in levels
        )

        if len(leaderboard) < 1:
            await message.edit(content=_("No results to display!"))
        else:
            embeds = LeaderboardPages(
                leaderboard, per_page=10, base=emb, emoji=self.emoji, stat=stat
            )
            menu = menus.MenuPages(
                source=embeds, timeout=300.0, message=message, clear_reactions_after=True
            )
            await message.edit(content=ctx.author.mention)
            await menu.show_page(0)
            await menu.start(ctx)
