import logging

import humanize
import os
from aiostream import stream
from typing import Final, Iterable, Literal

from discord.commands import ApplicationContext, slash_command, Option, OptionChoice
from discord.embeds import Embed
from discord.ext.commands import Bot, Context
from discord.ext.pages import Paginator

from trainerdex.faction import Faction
from trainerdex.leaderboard import BaseLeaderboard
from trainerdex.update import Level, get_level
from trainerdex_discord_bot.abc import MixinMeta
from trainerdex_discord_bot.constants import CUSTOM_EMOJI, STAT_VERBOSE_MAPPING, Stats
from trainerdex_discord_bot.embeds import BaseCard
from trainerdex_discord_bot.utils import chat_formatting

logger: logging.Logger = logging.getLogger(__name__)

POGOOCR_TOKEN_PATH: Final[str] = os.path.join(os.path.dirname(__file__), "data/key.json")


async def format_page(slice, stat: str, ctx: ApplicationContext) -> Embed:
    stat_emoji = ctx.bot.get_emoji(getattr(CUSTOM_EMOJI, stat.upper()).value)
    embed: Embed = await BaseCard(
        ctx, title=f"{stat_emoji} {STAT_VERBOSE_MAPPING.get(stat, stat)} Leaderboard"
    )
    stat_emoji = ctx.bot.get_emoji(getattr(CUSTOM_EMOJI, stat.upper()).value)
    for entry in slice:
        team_emoji = ctx.bot.get_emoji(
            getattr(CUSTOM_EMOJI, entry.faction.verbose_name.upper()).value
        )
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


async def get_pages(leaderboard: BaseLeaderboard, ctx: ApplicationContext) -> Iterable[Embed]:
    embeds: Iterable[Embed] = []
    async for page in stream.chunks(leaderboard, 10):
        embeds.append(await format_page(page, leaderboard.stat, ctx))
    return embeds


class Leaderboard(MixinMeta):
    @slash_command(name="leaderboard", description="Returns a leaderboard")
    async def leaderboard(
        self,
        ctx: ApplicationContext,
        leaderboard: Option(
            str,
            description="Leaderboard Class",
            choices=[
                OptionChoice(name="Server", value="guild"),
                OptionChoice(name="Global", value="global"),
            ],
            default="guild",
        ) = "guild",
        stat: Option(
            str,
            description="Stat",
            choices=[
                OptionChoice(name=verbose, value=stat)
                for stat, verbose in STAT_VERBOSE_MAPPING.items()
            ],
            default=Stats.TOTAL_XP.value,
        ) = Stats.TOTAL_XP.value,
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

        stat_emoji = self.bot.get_emoji(getattr(CUSTOM_EMOJI, stat.upper()).value)
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
            pages: Iterable[Embed] = await get_pages(leaderboard, ctx)

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
