import logging
import math
import os
from typing import Dict, Final, Iterable, Set, Union, Literal

from discord.embeds import Embed
from discord.emoji import Emoji
from discord.message import Message
import humanize
from discord.ext import commands
from discord.ext import pages

from trainerdex.faction import Faction
from trainerdex.leaderboard import GuildLeaderboard, Leaderboard as LeaderboardObject
from trainerdex.update import Level, get_level
from trainerdex.discord import converters
from trainerdex.discord.abc import MixinMeta
from trainerdex.discord.embeds import BaseCard
from trainerdex.discord.utils import chat_formatting

logger: logging.Logger = logging.getLogger(__name__)

POGOOCR_TOKEN_PATH: Final[str] = os.path.join(os.path.dirname(__file__), "data/key.json")


class LeaderboardPages(pages.AsyncIteratorPageSource):
    def __init__(self, *args, **kwargs) -> None:
        self.base: Embed = kwargs.pop("base")
        self.emoji: Dict[str, Union[str, Emoji]] = kwargs.pop("emoji")
        self.stat: Literal[
            "travel_km",
            "capture_total",
            "pokestops_visited",
            "total_xp",
        ] = kwargs.pop("stat")
        super().__init__(*args, **kwargs)

    async def format_page(self, menu, page) -> Dict[str, Embed]:
        emb: Embed = self.base.copy()
        for entry in page:
            emb.add_field(
                name="{pos} {handle} {faction}".format(
                    pos=f"{self.emoji.get('number', '#')} {entry.position}",
                    handle=entry.username,
                    faction=self.emoji.get(entry.faction.verbose_name.lower()),
                ),
                value="{value} • TL{level} • {dt}".format(
                    value=f"{self.emoji.get(self.stat)} {humanize.intcomma(entry.value)}",
                    level=entry.level,
                    dt=humanize.naturaldate(entry.last_updated),
                ),
                inline=False,
            )
        emb.set_footer(
            text="Page {page} of {pages} | {footer}".format(
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
        leaderboard: Literal["global", "guild", "server"] = "guild",
        stat: Literal["travel_km", "capture_total", "pokestops_visited", "total_xp"] = "total_xp",
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

        leaderboard: Literal["global", "guild", "server"] = leaderboard if ctx.guild else "global"
        is_guild: bool = True if leaderboard == "guild" else False

        # Convert stat_name for API
        stat: str = {
            "travel_km": "badge_travel_km",
            "capture_total": "badge_capture_total",
            "pokestops_visited": "badge_pokestops_visited",
            "total_xp": "total_xp",
        }[stat]

        stat_name: Dict[str, str] = {
            "badge_travel_km": "Distance Walked",
            "badge_capture_total": "Pokémon Caught",
            "badge_pokestops_visited": "PokéStops Visited",
            "total_xp": "Total XP",
        }

        factions: Set[Faction] = (
            {x for x in filters if isinstance(x, Faction)}
            if [x for x in filters if isinstance(x, Faction)]
            else {Faction(i) for i in range(0, 4)}
        )
        levels: Set[Level] = {x.level for x in filters if isinstance(x, Level)}
        if len(levels) > 1:
            levels: Iterable[Level] = range(
                min(levels),
                max(levels) + 1,
            )
        elif len(levels) == 1:
            levels: Iterable[Level] = range(levels.pop() + 1)
        else:
            levels: Iterable[Level] = range(1, 51)

        levels: Set[Level] = {get_level(level=i) for i in levels}

        leaderboard_title: str = (
            f"{self.emoji.get(stat, '')} {stat_name.get(stat, stat)} Leaderboard"
        )

        emb: BaseCard = await BaseCard(ctx, title=leaderboard_title)
        if leaderboard in ("guild", "server"):
            emb.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

        await ctx.tick()

        message: Message = await ctx.send(
            chat_formatting.loading("{tag} Downloading {leaderboard}…").format(
                tag=ctx.author.mention, leaderboard=leaderboard_title
            )
        )
        leaderboard: Union[
            LeaderboardObject,
            GuildLeaderboard,
        ] = await self.client.get_leaderboard(
            stat=stat,
            guild=ctx.guild if leaderboard in ("guild", "server") else None,
        )
        if is_guild:
            emb.description = (
                """Average {stat_name}: {stat_avg}
                Trainers: {stat_count}
                Sum of all Trainers: {stat_sum}"""
            ).format(
                stat_name=stat_name.get(stat, stat),
                stat_avg=chat_formatting.humanize_number(leaderboard.avg),
                stat_count=chat_formatting.humanize_number(leaderboard.count),
                stat_sum=chat_formatting.humanize_number(leaderboard.sum),
            )

        await message.edit(
            content=chat_formatting.loading("{tag} Filtering {leaderboard}…").format(
                tag=ctx.author.mention, leaderboard=leaderboard_title
            )
        )
        leaderboard.filter(lambda x: x.faction in factions).filter(
            lambda x: get_level(level=int(str(x.level).split("-")[0])) in levels
        )

        if len(leaderboard) < 1:
            await message.edit(content="No results to display!")
        else:
            embeds = LeaderboardPages(
                leaderboard, per_page=10, base=emb, emoji=self.emoji, stat=stat
            )
            menu = pages.MenuPages(
                source=embeds, timeout=300.0, message=message, clear_reactions_after=True
            )
            await message.edit(content=ctx.author.mention)
            await menu.show_page(0)
            await menu.start(ctx)
