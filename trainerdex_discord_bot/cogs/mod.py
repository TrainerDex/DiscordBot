from typing import Set
from discord import ApplicationContext, Member, Permissions, slash_command
from trainerdex_discord_bot.checks import has_permissions

from trainerdex_discord_bot.cogs.interface import Cog
from trainerdex_discord_bot.datatypes import GuildConfig
from trainerdex_discord_bot.utils.converters import get_trainer_from_user


class Mod(Cog):
    
    async def cog_check(self, ctx: ApplicationContext) -> bool:
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        if guild_config.assign_roles_on_join and not (manage_roles_perm := await has_permissions(Permissions(manage_roles=True))(ctx)):
            return False
            
        if guild_config.set_nickname_on_join and not (change_nickname_perm := await has_permissions(Permissions(change_nickname=True))(ctx)):
            return False
        
        if not (manage_server_perm := await has_permissions(Permissions(manage_server=True))(ctx)):
            return False
        
        return True
        
    
    
    @slash_command(name="grant-access", checks=[])
    async def slash__grant_access(self, ctx: ApplicationContext, member: Member) -> None:
        # Fetch the desired roles from the config
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)

        actions_commited: Set[str] = []
        if guild_config.assign_roles_on_join:
            await member.remove_roles(
                *guild_config.roles_to_assign_on_approval.remove, reason="Granting access"
            )
            actions_commited.add(
                f"""Removed roles {", ".join(guild_config.roles_to_assign_on_approval.remove)} from {member.display_name}."""
            )

            await member.add_roles(
                *guild_config.roles_to_assign_on_approval.add, reason="Granting access"
            )
            actions_commited.add(
                f"""Added roles {", ".join(guild_config.roles_to_assign_on_approval.remove)} to {member.display_name}."""
            )

        trainer = await get_trainer_from_user(self.client, member)
        if trainer:
            if guild_config.set_nickname_on_join:
                await member.edit(nick=trainer.nickname, reason="Granting access")
                actions_commited.add(
                    f"Set {member.display_name}'s nickname to {trainer.nickname}."
                )

            if guild_config.assign_roles_on_join:
                match trainer.faction:
                    case 1:
                        if guild_config.mystic_role:
                            await member.add_roles(guild_config.mystic_role, reason="Granting access")
                            actions_commited.add(f"Added tole {guild_config.mystic_role} to {member.display_name}.")
                    case 2:
                        if guild_config.valor_role:
                            await member.add_roles(guild_config.valor_role, reason="Granting access")
                            actions_commited.add(f"Added tole {guild_config.valor_role} to {member.display_name}.")
                    case 3:
                        if guild_config.instinct_role:
                            await member.add_roles(guild_config.instinct_role, reason="Granting access")
                            actions_commited.add(f"Added tole {guild_config.instinct_role} to {member.display_name}.")
        
        await ctx.respond("\n".join(actions_commited))
