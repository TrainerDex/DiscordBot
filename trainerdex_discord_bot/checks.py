from typing import Callable

from discord import ApplicationContext, ChannelType, Member, Permissions


def has_permissions(permissions: Permissions) -> Callable[[ApplicationContext], bool]:
    async def _has_permissions(ctx: ApplicationContext) -> bool:
        if not (channel := ctx.interaction.channel) or channel.type != ChannelType.text:
            return False

        is_owner_ = await is_owner(ctx)

        if not ctx.interaction.guild:
            return False

        is_guild_admin_ = await is_guild_admin(ctx)

        has_permissions_ = channel.permissions_for(ctx.author) >= permissions

        return is_owner_ or is_guild_admin_ or has_permissions_

    return _has_permissions


async def is_guild_admin(ctx: ApplicationContext) -> bool:
    if isinstance(ctx.author, Member):
        return ctx.author.guild_permissions.administrator or await is_owner(ctx)
    return False


async def is_owner(ctx: ApplicationContext) -> bool:
    return await ctx.bot.is_owner(ctx.author)
