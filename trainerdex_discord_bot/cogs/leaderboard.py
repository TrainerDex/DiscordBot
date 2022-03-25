from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Literal

import humanize
from aiostream import stream
from discord.commands import ApplicationContext, Option, OptionChoice, slash_command
from discord.embeds import Embed
from discord.ext.pages import Paginator
from lenum import LabeledEnum

from trainerdex_discord_bot.cogs.interface import Cog
from trainerdex_discord_bot.constants import CustomEmoji, Stats
from trainerdex_discord_bot.embeds import BaseCard

if TYPE_CHECKING:
    from trainerdex.leaderboard import BaseLeaderboard, LeaderboardEntry


class LeaderboardType(LabeledEnum):
    GUILD = "guild", "Discord Server"
    GLOBAL = "global", "Global"


class LeaderboardCog(Cog):
    async def _format_page(
        self,
        ctx: ApplicationContext,
        slice: Iterable[LeaderboardEntry],
        stat: str,
    ) -> Embed:
        stat_emoji = getattr(CustomEmoji, stat.upper(), CustomEmoji.TRAINERDEX).value
        embed: Embed = await BaseCard(
            self._common,
            ctx,
            title=f"{stat_emoji} {Stats.__members__.get(stat, stat)} Leaderboard",
        )
        for entry in slice:
            team_emoji = getattr(
                CustomEmoji, entry.faction.verbose_name.upper(), CustomEmoji.TRAINERDEX
            ).value
            embed.add_field(
                name=f"# {entry.position} {entry.username} {team_emoji}",
                value=f"{stat_emoji} {humanize.intcomma(entry.value)} • {humanize.naturaldate(entry.last_updated)}",
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

        leaderboard: BaseLeaderboard = await self.client.get_leaderboard(
            stat=stat,
            guild=ctx.guild if leaderboard in ("guild", "server") else None,
        )

        await ctx.defer()

        if len(leaderboard) < 1:
            await ctx.followup.send(content="No results to display!")
        else:
            pages: Iterable[Embed] = await self._get_pages(ctx, leaderboard)

            for embed in pages:
                if leaderboard == "guild":
                    embed.set_author(
                        name=ctx.interaction.guild.name, icon_url=ctx.interaction.guild.icon.url
                    )
                    embed.description = (
                        """Average {stat_name}: {stat_avg}
                        Trainers: {stat_count}
                        Sum of all Trainers: {stat_sum}"""
                    ).format(
                        stat_name=Stats[getattr(Stats, stat)],
                        stat_avg=humanize.intcomma(leaderboard.avg),
                        stat_count=humanize.intcomma(leaderboard.count),
                        stat_sum=humanize.intcomma(leaderboard.sum),
                    )

            paginator = Paginator(pages, disable_on_timeout=True)
            await paginator.respond(ctx.interaction)
