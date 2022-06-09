import discord.errors
from discord import ApplicationContext, Member, Permissions, slash_command

from trainerdex_discord_bot.checks import has_permissions
from trainerdex_discord_bot.cogs.interface import Cog
from trainerdex_discord_bot.datatypes import GuildConfig
from trainerdex_discord_bot.utils.converters import get_trainer_from_user


class ModCog(Cog):
    async def cog_check(self, ctx: ApplicationContext) -> bool:
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        if guild_config.assign_roles_on_join and not (
            await has_permissions(Permissions(manage_roles=True))(ctx)
        ):
            return False

        if guild_config.set_nickname_on_join and not (
            await has_permissions(Permissions(change_nickname=True))(ctx)
        ):
            return False

        if not (await has_permissions(Permissions(manage_server=True))(ctx)):
            return False

        return True

    @slash_command(name="grant-access", checks=[])
    async def slash__grant_access(self, ctx: ApplicationContext, member: Member) -> None:
        # Fetch the desired roles from the config
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)

        reason = (
            f"{ctx.author} used the /grant-access command to grant {member} access to this guild."
        )

        rm_roles, add_roles, nickname_changed = set(), set(), False
        if guild_config.assign_roles_on_join:
            try:
                if rm_roles := set(guild_config.roles_to_assign_on_approval.remove):
                    await member.remove_roles(*rm_roles, reason=reason)

                if add_roles := set(guild_config.roles_to_assign_on_approval.add):
                    await member.add_roles(*add_roles, reason=reason)
            except discord.errors.Forbidden:
                pass

        trainer = await get_trainer_from_user(self.client, member)
        if trainer:
            if guild_config.set_nickname_on_join:
                try:
                    await member.edit(nick=trainer.nickname, reason=reason)
                except discord.errors.Forbidden:
                    pass
                else:
                    nickname_changed = True

            if guild_config.assign_roles_on_join:
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
            actions_commited.append("Nickname changed to {}".format(trainer.nickname))
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
