from typing import Callable

from discord import ApplicationContext, ChannelType, Permissions


def has_permissions(permissions: Permissions) -> Callable[[ApplicationContext], bool]:
    async def _has_permissions_or_owner(ctx: ApplicationContext) -> bool:
        # is_owner_ = await is_owner(ctx)
        is_owner_ = False

        if not ctx.interaction.guild:
            return False

        is_guild_admin_ = await is_guild_admin(ctx)

        if not (channel := ctx.interaction.channel) or channel.type != ChannelType.text:
            return False

        has_permissions_ = channel.permissions_for(ctx.author) >= permissions

        return is_owner_ or is_guild_admin_ or has_permissions_

    return _has_permissions_or_owner


async def is_guild_admin(ctx: ApplicationContext) -> bool:
    return ctx.author.guild_permissions.administrator


async def is_owner(ctx: ApplicationContext) -> bool:
    return await ctx.bot.is_owner(ctx.author)
