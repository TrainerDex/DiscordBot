import datetime
import logging
from discord.embeds import Embed
from discord.message import Message
from redbot.core import commands
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf
from trainerdex.trainer import Trainer
from trainerdex.update import Update

from . import converters
from .abc import MixinMeta
from .embeds import ProfileCard
from .utils import loading

logger: logging.Logger = logging.getLogger(__name__)
_: Translator = Translator("TrainerDex", __file__)


class Post(MixinMeta):
    @commands.group(name="update", case_insensitive=True)
    async def update(self, ctx: commands.Context) -> None:
        pass

    @update.command(
        name="gyms", brief="Run this after posting your XP for the best results.", hidden=True
    )
    async def post__gyms(
        self,
        ctx: commands.Context,
        value: int,
    ) -> None:
        async with ctx.typing():
            try:
                trainer: Trainer = await converters.TrainerConverter().convert(
                    ctx, ctx.author, cli=self.client
                )
            except commands.BadArgument:
                await ctx.send(cf.error("No profile found."))
                return

            await trainer.fetch_updates()
            latest_update: Update = trainer.get_latest_update()
            if latest_update and latest_update.update_time > (
                datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(hours=12)
            ):
                if latest_update.gymbadges_gold:
                    post_new: bool = True
                else:
                    post_new: bool = False
                    update: Update = latest_update
            else:
                post_new: bool = True

            if post_new:
                message: Message = await ctx.send(loading(_("Creating a new post…")))
                update: Update = await trainer.post(
                    stats={"gymbadges_gold": value},
                    data_source="ts_social_discord",
                    update_time=ctx.message.created_at,
                    submission_date=datetime.datetime.now(tz=datetime.timezone.utc),
                )
            else:
                message: Message = await ctx.send(
                    loading(_("Updating a post from earlier today…"))
                )
                await update.edit(
                    **{"update_time": ctx.message.created_at, "gymbadges_gold": value}
                )

            if ctx.guild and not trainer.is_visible:
                await message.edit(_("Sending in DMs"))
                message: Message = await ctx.author.send(content=loading(_("Loading output…")))

            await message.edit(content=loading(_("Loading output…")))
            embed: Embed = await ProfileCard(
                ctx=ctx,
                client=self.client,
                trainer=trainer,
                update=update,
                emoji=self.emoji,
            )
            await message.edit(content=loading(_("Loading output…")))
            await embed.show_progress()
            await message.edit(
                content=loading(_("Loading output…")),
                embed=embed,
            )
            await embed.add_leaderboard()
            if ctx.guild:
                await message.edit(embed=embed)
                await embed.add_guild_leaderboard(ctx.guild)
            await message.edit(content=None, embed=embed)
