import datetime
import logging
from discord.embeds import Embed
from discord.message import Message
from discord.ext import commands
from trainerdex_discord_bot.utils import chat_formatting
from trainerdex.trainer import Trainer
from trainerdex.update import Update

from trainerdex_discord_bot import converters
from trainerdex_discord_bot.abc import MixinMeta
from trainerdex_discord_bot.embeds import ProfileCard

logger: logging.Logger = logging.getLogger(__name__)


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
                await ctx.send(chat_formatting.error("No profile found."))
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
                message: Message = await ctx.send(chat_formatting.loading("Creating a new post…"))
                update: Update = await trainer.post(
                    stats={"gymbadges_gold": value},
                    data_source="ts_social_discord",
                    update_time=ctx.message.created_at,
                    submission_date=datetime.datetime.now(tz=datetime.timezone.utc),
                )
            else:
                message: Message = await ctx.send(
                    chat_formatting.loading("Updating a post from earlier today…")
                )
                await update.edit(
                    **{"update_time": ctx.message.created_at, "gymbadges_gold": value}
                )

            if ctx.guild and not trainer.is_visible:
                await message.edit("Sending in DMs")
                message: Message = await ctx.author.send(
                    content=chat_formatting.loading("Loading output…")
                )

            await message.edit(content=chat_formatting.loading("Loading output…"))
            embed: Embed = await ProfileCard(
                ctx,
                client=self.client,
                trainer=trainer,
                update=update,
            )
            await message.edit(content=chat_formatting.loading("Loading output…"))
            await embed.show_progress()
            await message.edit(
                content=chat_formatting.loading("Loading output…"),
                embed=embed,
            )
            await embed.add_leaderboard()
            if ctx.guild:
                await message.edit(embed=embed)
                await embed.add_guild_leaderboard(ctx.guild)
            await message.edit(content=None, embed=embed)
