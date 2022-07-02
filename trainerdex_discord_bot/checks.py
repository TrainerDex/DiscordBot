from typing import Callable, Optional

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


async def check_member_privilage(
    self,
    ctx: ApplicationContext,
    /,
    *,
    member: Optional[Member] = None,
) -> bool:
    """A coroutine that returns whether the user is considered a privilaged or not.

    Checks if the user is a mod by checking if the user has one of the mod roles as defined in the settings.
    Also checks if the user is the owner of the bot, an admin of the guild or has manage_guild permission.
    If any of these checks pass, the user is considered privilaged.

    """
    if member is None:
        member = ctx.author

    if await ctx.bot.is_owner(member):
        return True

    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        return True

    for role_id in (await self.config.get_guild(member.guild.id)).mod_role_ids:
        if member.get_role(role_id):
            return True

    return False
