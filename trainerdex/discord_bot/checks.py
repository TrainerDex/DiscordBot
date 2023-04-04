from discord import ApplicationContext, Member

from trainerdex.discord_bot.config import Config


async def check_member_privilage(
    ctx: ApplicationContext,
    /,
    *,
    member: Member | None = None,
) -> bool:
    """A coroutine that returns whether the user is considered a privilaged or not.

    Checks if the user is a mod by checking if the user has one of the mod roles as defined in the settings.
    Also checks if the user is the owner of the bot, an admin of the server or has manage_guild permission.
    If any of these checks pass, the user is considered privilaged.

    """
    if member is None:
        member = ctx.author

    if await ctx.bot.is_owner(member):
        return True

    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        return True

    config = Config()
    return any(member.get_role(role_id) for role_id in (await config.get_guild(member.guild.id)).mod_role_ids)
