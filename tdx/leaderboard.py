import logging
import os
from typing import Final, Optional, Union

import humanize
from redbot.core import commands
from redbot.core.commands.converter import Literal
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf, menus

import trainerdex as client
from . import converters
from .abc import MixinMeta
from .embeds import BaseCard
from .utils import append_icon, loading, quote

log: logging.Logger = logging.getLogger(__name__)
POGOOCR_TOKEN_PATH: Final = os.path.join(os.path.dirname(__file__), "data/key.json")
_ = Translator("TrainerDex", __file__)


class Leaderboard(MixinMeta):
    @commands.command(name="leaderboard", aliases=["lb", "LB"])
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
            `filters`: Union[Faction, Level]
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
            levels = range(min(levels), max(levels) + 1,)
        elif len(levels) == 1:
            levels = range(levels.pop() + 1)
        else:
            levels = range(1, 41)

        levels = {client.update.get_level(level=i) for i in levels}

        leaderboard_title = append_icon(
            icon=self.emoji.get(stat[0], ""), text=_("{stat} Leaderboard").format(stat=stat[1]),
        )
        BASE_EMBED = await BaseCard(ctx, title=leaderboard_title)
        if leaderboard in ("guild", "server"):
            BASE_EMBED.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

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

        await message.edit(
            content=loading(_("{tag} Processing results!")).format(tag=ctx.author.mention)
        )
        embeds = []
        working_embed = BASE_EMBED.copy()

        async for entry in leaderboard:
            """If embed at field limit, append to embeds list and start a fresh embed"""
            if len(working_embed.fields) < 15:
                working_embed.add_field(
                    name="{pos} {handle} {faction}".format(
                        pos=append_icon(self.emoji.get("number", "#"), entry.position),
                        handle=entry.username,
                        faction=self.emoji.get(entry.faction.verbose_name.lower()),
                    ),
                    value="{value} • TL{level} • {dt}".format(
                        value=append_icon(
                            self.emoji.get(stat[0]), cf.humanize_number(entry.total_xp)
                        ),
                        level=entry.level,
                        dt=humanize.naturaldate(entry.last_updated),
                    ),
                    inline=False,
                )
            if len(working_embed.fields) == 15:
                embeds.append(working_embed)
                await message.edit(
                    content=loading(_("{tag} Processing results ({pages} pages)")).format(
                        tag=ctx.author.mention, pages=len(embeds)
                    )
                )
                working_embed = BASE_EMBED.copy()
        if len(working_embed.fields) > 0:
            embeds.append(working_embed)

        if ctx.channel.permissions_for(ctx.me).external_emojis:
            menu_controls = (
                {
                    self.emoji.get("previous"): menus.prev_page,
                    "❌": menus.close_menu,
                    self.emoji.get("next"): menus.next_page,
                }
                if len(embeds) > 1
                else {"❌": menus.close_menu}
            )
        else:
            menu_controls = menus.DEFAULT_CONTROLS if len(embeds) > 1 else {"❌": menus.close_menu}

        if embeds:
            if len(menu_controls.keys()) == 3:
                controls_text = _(
                    "{tag} Tap {close} to close the leaderboard, navigate with {prev} and {next}."
                    " There is a 5 minute timeout."
                ).format(
                    tag=ctx.author.mention,
                    prev=list(menu_controls.keys())[0],
                    close=list(menu_controls.keys())[1],
                    next=list(menu_controls.keys())[2],
                )
            else:
                controls_text = _(
                    "{tag} Tap {close} to close the leaderboard. There is a 5 minute timeout."
                ).format(tag=ctx.author.mention, close=list(menu_controls.keys())[0])

            await message.edit(content="\n".join([quote(ctx.message.content), controls_text]))
            await ctx.message.delete()
        else:
            await message.edit(content="No results to display")
            return

        menus.start_adding_reactions(message, menu_controls.keys())
        await menus.menu(ctx, embeds, menu_controls, message=message, timeout=300.0)
