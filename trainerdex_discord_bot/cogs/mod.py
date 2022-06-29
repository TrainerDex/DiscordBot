from typing import Optional

import discord.errors
from discord import ApplicationContext, Member, slash_command

from trainerdex_discord_bot.cogs.interface import Cog
from trainerdex_discord_bot.datatypes import GuildConfig
from trainerdex_discord_bot.utils.converters import get_trainer_from_user


class ModCog(Cog):
    async def cog_check(self, ctx: ApplicationContext) -> bool:
        """A special method that registers as a :func:`~discord.ext.commands.check`
        for every command and subcommand in this cog.

        This function **can** be a coroutine and must take a sole parameter,
        ``ctx``, to represent the :class:`.Context`.
        """
        return self.check_member_privilage(ctx)

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

    async def allowed_to_rename(self, ctx: ApplicationContext) -> bool:
        if not (await self.config.get_guild(ctx.guild.id)).set_nickname_on_join:
            return False

        if self.check_member_privilage(ctx):
            return True

        if ctx.author.guild_permissions.manage_nicknames:
            return True

        return False

    async def allowed_to_assign_roles(self, ctx: ApplicationContext) -> bool:
        if not (await self.config.get_guild(ctx.guild.id)).assign_roles_on_join:
            return False

        if self.check_member_privilage(ctx):
            return True

        if ctx.author.guild_permissions.manage_roles:
            return True

        return False

    @slash_command(name="grant-access", checks=[])
    async def slash__grant_access(self, ctx: ApplicationContext, member: Member) -> None:
        reason = (
            f"{ctx.author} used the /grant-access command to grant {member} access to this guild."
        )

        allowed_to_rename: bool = await self.allowed_to_rename(ctx)
        allowed_to_assign_roles: bool = await self.allowed_to_assign_roles(ctx)

        rm_roles, add_roles, nickname_changed = set(), set(), False

        if allowed_to_assign_roles:
            guild_config: GuildConfig = await self.config.get_guild(ctx.guild)

            try:
                if rm_roles := set(guild_config.roles_to_assign_on_approval.remove):
                    await member.remove_roles(*rm_roles, reason=reason)

                if add_roles := set(guild_config.roles_to_assign_on_approval.add):
                    await member.add_roles(*add_roles, reason=reason)
            except discord.errors.Forbidden:
                pass

        trainer = await get_trainer_from_user(self.client, member)
        if trainer:
            if allowed_to_rename:
                try:
                    await member.edit(nick=trainer.nickname, reason=reason)
                except discord.errors.Forbidden:
                    pass
                else:
                    nickname_changed = True

            if allowed_to_assign_roles:
                try:
                    match trainer.faction:
                        case 1:
                            if guild_config.mystic_role:
                                await member.add_roles(guild_config.mystic_role, reason=reason)
                                add_roles.add(guild_config.mystic_role)
                        case 2:
                            if guild_config.valor_role:
                                await member.add_roles(guild_config.valor_role, reason=reason)
                                add_roles.add(guild_config.valor_role)
                        case 3:
                            if guild_config.instinct_role:
                                await member.add_roles(guild_config.instinct_role, reason=reason)
                                add_roles.add(guild_config.instinct_role)
                except discord.errors.Forbidden:
                    pass

        actions_commited = []
        if nickname_changed:
            actions_commited.append(f"Nickname changed to {trainer.nickname}")

        if allowed_to_assign_roles:
            if rm_roles:
                actions_commited.append(
                    "Removed roles: {}".format(
                        ", ".join([ctx.guild.get_role(role_id).name for role_id in rm_roles])
                    )
                )

            if add_roles:
                actions_commited.append(
                    "Added roles: {}".format(
                        ", ".join([ctx.guild.get_role(role_id).name for role_id in add_roles])
                    )
                )

        if actions_commited:
            await ctx.respond(
                f"`/grant-access` run on {member.mention}\n" + "\n".join(actions_commited)
            )
        else:
            await ctx.respond("No actions were committed.")
