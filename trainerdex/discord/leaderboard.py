import logging
import humanize
import os
from itertools import islice
from typing import AsyncIterable, Final, Iterable, Union, Literal

from discord.embeds import Embed
from discord.ext.commands import Bot, command, Context
from discord.ext.pages import Paginator
from discord.message import Message

from trainerdex.faction import Faction
from trainerdex.leaderboard import BaseLeaderboard
from trainerdex.update import Level, get_level
from trainerdex.discord import converters
from trainerdex.discord.abc import MixinMeta
from trainerdex.discord.constants import CUSTOM_EMOJI
from trainerdex.discord.embeds import BaseCard
from trainerdex.discord.utils import chat_formatting

logger: logging.Logger = logging.getLogger(__name__)

POGOOCR_TOKEN_PATH: Final[str] = os.path.join(os.path.dirname(__file__), "data/key.json")


async def split_async_iter(n: int, iterable: AsyncIterable) -> AsyncIterable:
    i = iter(iterable)
    piece = list(islice(i, n))
    while piece:
        yield piece
        piece = list(islice(i, n))


async def format_page(slice, stat: str, bot: Bot, base_embed: Embed = Embed()) -> Embed:
    embed: Embed = base_embed.copy()
    stat_emoji = bot.get_emoji(getattr(CUSTOM_EMOJI, stat.upper()))
    for entry in slice:
        team_emoji = bot.get_emoji(getattr(CUSTOM_EMOJI, entry.faction.verbose_name.upper()))
        embed.add_field(
            name=f"# {entry.position} {entry.username} {team_emoji}",
            value=f"{stat_emoji} {humanize.intcomma(entry.value)} • TL{entry.level} • {humanize.naturaldate(entry.last_updated)}",
            inline=False,
        )
    embed.set_footer(
        text=embed.footer.text,
        icon_url=embed.footer.icon_url,
    )
    return embed


async def get_pages(
    leaderboard: BaseLeaderboard, bot: Bot, base_embed: Embed = Embed()
) -> Iterable[Embed]:
    embeds: Iterable[Embed] = []
    for page in await split_async_iter(10, leaderboard):
        embeds.append(await format_page(page, leaderboard.stat, bot, base_embed))
    return embeds


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

    @command(name="leaderboard", aliases=list(set(leaderboard_aliases)))
    async def leaderboard(
        self,
        ctx: Context,
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

        stat_name: dict[str, str] = {
            "badge_travel_km": "Distance Walked",
            "badge_capture_total": "Pokémon Caught",
            "badge_pokestops_visited": "PokéStops Visited",
            "total_xp": "Total XP",
        }

        factions: set[Faction] = (
            {x for x in filters if isinstance(x, Faction)}
            if [x for x in filters if isinstance(x, Faction)]
            else {Faction(i) for i in range(0, 4)}
        )
        levels: set[Level] = {x.level for x in filters if isinstance(x, Level)}
        if len(levels) > 1:
            levels: Iterable[Level] = range(
                min(levels),
                max(levels) + 1,
            )
        elif len(levels) == 1:
            levels: Iterable[Level] = range(levels.pop() + 1)
        else:
            levels: Iterable[Level] = range(1, 51)

        levels: set[Level] = {get_level(level=i) for i in levels}

        stat_emoji = self.bot.get_emoji(getattr(CUSTOM_EMOJI, stat.upper()))
        leaderboard_title: str = f"{stat_emoji} {stat_name.get(stat, stat)} Leaderboard"

        embed: BaseCard = await BaseCard(ctx, title=leaderboard_title)
        if leaderboard in ("guild", "server"):
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

        await ctx.tick()

        reply: Message = await ctx.reply(
            chat_formatting.loading(f"Downloading {leaderboard_title}…")
        )
        leaderboard: BaseLeaderboard = await self.client.get_leaderboard(
            stat=stat,
            guild=ctx.guild if leaderboard in ("guild", "server") else None,
        )
        if is_guild:
            embed.description = (
                """Average {stat_name}: {stat_avg}
                Trainers: {stat_count}
                Sum of all Trainers: {stat_sum}"""
            ).format(
                stat_name=stat_name.get(stat, stat),
                stat_avg=humanize.intcomma(leaderboard.avg),
                stat_count=humanize.intcomma(leaderboard.count),
                stat_sum=humanize.intcomma(leaderboard.sum),
            )

        await reply.edit(
            content=chat_formatting.loading("{tag} Filtering {leaderboard}…").format(
                tag=ctx.author.mention, leaderboard=leaderboard_title
            )
        )
        leaderboard.filter(lambda x: x.faction in factions).filter(
            lambda x: get_level(level=int(str(x.level).split("-")[0])) in levels
        )

        if len(leaderboard) < 1:
            await reply.edit(content="No results to display!")
        else:
            pages: Iterable[Embed] = await get_pages(leaderboard, self.bot, base_embed=embed)

            paginator = Paginator(pages, disable_on_timeout=True)
            await paginator.send(ctx)
