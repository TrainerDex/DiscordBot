from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Literal

import humanize
from aiostream import stream
from discord.commands import ApplicationContext, Option, OptionChoice, slash_command
from discord.embeds import Embed
from discord.ext.pages import Paginator
from lenum import LabeledEnum

from trainerdex.leaderboard import GuildLeaderboard

from trainerdex_discord_bot.cogs.interface import Cog
from trainerdex_discord_bot.constants import CustomEmoji, Stats
from trainerdex_discord_bot.embeds import BaseCard
from trainerdex_discord_bot.utils.chat_formatting import format_numbers
from trainerdex_discord_bot.utils.general import send

if TYPE_CHECKING:
    from trainerdex.leaderboard import BaseLeaderboard, LeaderboardEntry


class LeaderboardType(LabeledEnum):
    GUILD = "guild", "Discord Server"
    GLOBAL = "global", "Global"


class LeaderboardCog(Cog):
    async def _format_page(
        self,
        ctx: ApplicationContext,
        leaderboard: BaseLeaderboard,
        slice: Iterable[LeaderboardEntry],
    ) -> Embed:
        stat_emoji = getattr(CustomEmoji, leaderboard.stat.upper(), CustomEmoji.TRAINERDEX).value
        stat_name = Stats.__members__.get(leaderboard.stat, leaderboard.stat)
        embed: Embed = await BaseCard(
            self._common,
            ctx,
            title=f"{stat_emoji} {stat_name} Leaderboard",
            description=(
                """Trainer Count: {stat_count}
                {stat_emoji} Min: {stat_min}
                {stat_emoji} Avg: {stat_avg}
                {stat_emoji} Max: {stat_max}
                {stat_emoji} Sum: {stat_sum}"""
            ).format(
                stat_emoji=stat_emoji,
                stat_avg=format_numbers(leaderboard.avg),
                stat_count=format_numbers(leaderboard.count),
                stat_sum=format_numbers(leaderboard.sum),
                stat_min=format_numbers(leaderboard.min),
                stat_max=format_numbers(leaderboard.max),
            ),
        )

        if isinstance(leaderboard, GuildLeaderboard):
            embed.set_author(
                name=ctx.interaction.guild.name, icon_url=ctx.interaction.guild.icon.url
            )

        for entry in slice:
            team_emoji = getattr(
                CustomEmoji, entry.faction.verbose_name.upper(), CustomEmoji.TRAINERDEX
            ).value
            embed.add_field(
                name=f"# {entry.position} {entry.username} {team_emoji}",
                value=f"{stat_emoji} {format_numbers(entry.value)} • {humanize.naturaldate(entry.last_updated)}",
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
            embeds.append(await self._format_page(ctx, leaderboard, page))
        return embeds

    @slash_command(
        name="leaderboard",
        description="Returns a leaderboard",
        options=[
            Option(
                str,
                name="leaderboard",
                choices=[OptionChoice(name, value) for value, name in LeaderboardType],
                default=LeaderboardType.GUILD,
            ),
            Option(
                str,
                name="stat",
                choices=[OptionChoice(name, value) for value, name in Stats][:25],
                default=Stats.TOTAL_XP,
            ),
        ],
    )
    async def leaderboard(
        self,
        ctx: ApplicationContext,
        leaderboard: str,
        stat: str,
    ) -> None:
        leaderboard: Literal["global", "guild"] = ctx.interaction.guild and leaderboard or "global"

        leaderboard_data: BaseLeaderboard = await self.client.get_leaderboard(
            stat=stat,
            guild=ctx.guild if leaderboard in ("guild", "server") else None,
        )

        await ctx.defer()

        if len(leaderboard_data) < 1:
            await send(ctx, content="No results to display!")
        else:
            pages: Iterable[Embed] = await self._get_pages(ctx, leaderboard_data)
            paginator = Paginator(pages, disable_on_timeout=True)
            await paginator.respond(ctx.interaction)
