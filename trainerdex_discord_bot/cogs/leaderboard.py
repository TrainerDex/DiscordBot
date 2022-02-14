from __future__ import annotations

import logging
import humanize
from aiostream import stream
from typing import TYPE_CHECKING, Iterable, Literal

from discord.commands import ApplicationContext, slash_command, Option, OptionChoice
from discord.embeds import Embed
from discord.ext.commands import Bot, Cog
from discord.ext.pages import Paginator


from trainerdex.faction import Faction
from trainerdex.update import Level, get_level
from trainerdex_discord_bot.constants import CustomEmoji, STAT_VERBOSE_MAPPING, Stats
from trainerdex_discord_bot.embeds import BaseCard
from trainerdex_discord_bot.utils import chat_formatting

if TYPE_CHECKING:
    from trainerdex.client import Client
    from trainerdex.leaderboard import BaseLeaderboard
    from trainerdex_discord_bot.config import Config
    from trainerdex_discord_bot.datatypes import Common


logger: logging.Logger = logging.getLogger(__name__)


class LeaderboardCog(Cog):
    def __init__(self, common: Common) -> None:
        logger.info(f"Initializing {self.__class__.__cog_name__} cog...")
        self._common: Common = common
        self.bot: Bot = common.bot
        self.config: Config = common.config
        self.client: Client = common.client

    async def _format_page(
        self,
        ctx: ApplicationContext,
        slice,
        stat: str,
    ) -> Embed:
        stat_emoji = getattr(CustomEmoji, stat.upper()).value
        embed: Embed = await BaseCard(
            self._common,
            ctx,
            title=f"{stat_emoji} {STAT_VERBOSE_MAPPING.get(stat, stat)} Leaderboard",
        )
        stat_emoji = getattr(CustomEmoji, stat.upper()).value
        for entry in slice:
            team_emoji = getattr(CustomEmoji, entry.faction.verbose_name.upper()).value
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

    async def _get_pages(
        self,
        ctx: ApplicationContext,
        leaderboard: BaseLeaderboard,
    ) -> Iterable[Embed]:
        embeds: Iterable[Embed] = []
        async for page in stream.chunks(leaderboard, 10):
            embeds.append(await self._format_page(ctx, page, leaderboard.stat))
        return embeds

    @slash_command(
        name="leaderboard",
        description="Returns a leaderboard",
        options=[
            Option(
                str,
                name="leaderboard",
                choices=[
                    OptionChoice(name="Server", value="guild"),
                    OptionChoice(name="Global", value="global"),
                ],
                default="guild",
            ),
            Option(
                str,
                name="stat",
                choices=[
                    OptionChoice(name=verbose, value=stat)
                    for stat, verbose in STAT_VERBOSE_MAPPING.items()
                ],
                default=Stats.TOTAL_XP.value,
            ),
        ],
    )
    async def leaderboard(
        self,
        ctx: ApplicationContext,
        leaderboard: str = "guild",
        stat: str = Stats.TOTAL_XP.value,
    ) -> None:
        leaderboard: Literal["global", "guild"] = (
            leaderboard if ctx.interaction.guild else "global"
        )
        is_guild: bool = True if leaderboard == "guild" else False

        filters = []

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

        stat_emoji = getattr(CustomEmoji, stat.upper()).value
        leaderboard_title: str = f"{stat_emoji} {STAT_VERBOSE_MAPPING.get(stat, stat)} Leaderboard"

        leaderboard: BaseLeaderboard = await self.client.get_leaderboard(
            stat=stat,
            guild=ctx.guild if leaderboard in ("guild", "server") else None,
        )

        await ctx.respond(content=chat_formatting.loading(f"Loading {leaderboard_title}…"))
        leaderboard.filter(lambda x: x.faction in factions).filter(
            lambda x: get_level(level=int(str(x.level).split("-")[0])) in levels
        )

        if len(leaderboard) < 1:
            await ctx.respond(content="No results to display!")
        else:
            pages: Iterable[Embed] = await self._get_pages(ctx, leaderboard)

            for embed in pages:
                if is_guild:
                    embed.set_author(
                        name=ctx.interaction.guild.name, icon_url=ctx.interaction.guild.icon.url
                    )
                    embed.description = (
                        """Average {stat_name}: {stat_avg}
                        Trainers: {stat_count}
                        Sum of all Trainers: {stat_sum}"""
                    ).format(
                        stat_name=STAT_VERBOSE_MAPPING.get(stat, stat),
                        stat_avg=humanize.intcomma(leaderboard.avg),
                        stat_count=humanize.intcomma(leaderboard.count),
                        stat_sum=humanize.intcomma(leaderboard.sum),
                    )

            paginator = Paginator(pages, disable_on_timeout=True)
            await paginator.respond(ctx.interaction)
