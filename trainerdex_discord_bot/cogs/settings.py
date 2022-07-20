from typing import TYPE_CHECKING, List

from discord import (
    ApplicationContext,
    Option,
    OptionChoice,
    Permissions,
    SlashCommandGroup,
)
from discord.role import Role

from trainerdex_discord_bot.checks import check_member_privilage
from trainerdex_discord_bot.cogs.interface import Cog
# from trainerdex_discord_bot.datatypes import GlobalConfig
from trainerdex_discord_bot.utils.chat_formatting import error, info, success
from trainerdex_discord_bot.utils.general import send

if TYPE_CHECKING:
    from trainerdex_discord_bot.datatypes import GuildConfig


class SettingsCog(Cog):
    guild_config = SlashCommandGroup(
        "server-config",
        "Set server settings",
        checks=[check_member_privilage],
        default_member_permissions=Permissions(0x20),
    )
    # _set_channel = SlashCommandGroup(
    #     "channel-config",
    #     "Set channel settings",
    #     checks=[check_member_privilage],
    # )
    # _set_global = SlashCommandGroup(
    #     "global-config",
    #     "Set global settings",
    #     checks=[is_owner],
    # )

    @guild_config.command(name="assign-roles-on-join", checks=[check_member_privilage])
    async def guild_config__assign_roles_on_join(self, ctx: ApplicationContext, value: bool) -> None:
        """Modify the roles of members when they're approved.

        This is useful for granting users access to the rest of the server.
        """
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        guild_config.assign_roles_on_join = value
        await self.config.set_guild(guild_config)

        await send(
            ctx,
            f"Set `assign_roles_on_join` to `{value}`.",
            ephemeral=True,
        )

    @guild_config.command(name="set-nickname-on-join", checks=[check_member_privilage])
    async def guild_config__set_nickname_on_join(self, ctx: ApplicationContext, value: bool) -> None:
        """Modify the nickname of members when they're approved.

        This is useful for ensuring players can be easily identified.
        """
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        guild_config.set_nickname_on_join = value
        await self.config.set_guild(guild_config)

        await send(
            ctx,
            f"Set `set_nickname_on_join` to `{value}`.",
            ephemeral=True,
        )

    @guild_config.command(name="set-nickname-on-update", checks=[check_member_privilage])
    async def guild_config__set_nickname_on_update(
        self, ctx: ApplicationContext, value: bool
    ) -> None:
        """Modify the nickname of members when they update their Total XP.

        This is useful for setting levels in their name.
        """
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        guild_config.set_nickname_on_update = value
        await self.config.set_guild(guild_config)

        await send(
            ctx,
            f"Set `set_nickname_on_update` to `{value}`.",
            ephemeral=True,
        )

    @guild_config.command(
        name="access-roles",
        options=[
            Option(
                str,
                name="action",
                choices=[
                    OptionChoice(name="Add role", value="append"),
                    OptionChoice(name="Remove role", value="unappend"),
                    OptionChoice(name="View roles", value="view"),
                ],
            ),
            Option(
                str,
                name="array",
                choices=[
                    OptionChoice(name="Grant roles", value="grant"),
                    OptionChoice(name="Revoke roles", value="revoke"),
                ],
            ),
            Option(
                Role,
                name="role",
                required=False,
            ),
        ],
        checks=[check_member_privilage],
    )
    async def guild_config__access_roles(
        self, ctx: ApplicationContext, action: str, array: str, role: Role | None = None
    ):
        if action != "view" and role is None:
            await ctx.send(
                error(
                    "If you are appending/unappending to the grant/revoke lists, you must include a role to parameter."
                )
            )
            return

        await ctx.defer()

        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)

        if array == "grant":
            role_list: List[Role] = guild_config.roles_to_assign_on_approval.add or []
        elif array == "revoke":
            role_list: List[Role] = guild_config.roles_to_assign_on_approval.remove or []
        else:
            raise ValueError()

        if action == "view":
            message = "The following roles will be modified for a user when they are granted access to the guild:\n{}"
            set_of_roles = {
                f"{ctx.guild.get_role(role_id).name or ''} ({role_id})" for role_id in role_list
            }
            await ctx.followup.send(info(message.format(", ".join(set_of_roles))))
        elif action == "append":
            if role.id not in role_list:
                role_list.append(role.id)

            message = "{} was appended to the list. The list is now: {}"
            set_of_roles = {
                f"{ctx.guild.get_role(role_id).name or ''} ({role_id})" for role_id in role_list
            }
            await ctx.followup.send(success(message.format(role, ", ".join(set_of_roles))))
        elif action == "unappend":
            while role.id in role_list:
                role_list.remove(role.id)

            message = "{} was removed from the list. The list is now: {}"
            set_of_roles = {
                f"{ctx.guild.get_role(role_id).name or ''} ({role_id})" for role_id in role_list
            }
            await ctx.followup.send(success(message.format(role, ", ".join(set_of_roles))))

        if array == "grant":
            guild_config.roles_to_assign_on_approval.add = list(set(role_list))
        elif array == "revoke":
            guild_config.roles_to_assign_on_approval.remove = list(set(role_list))
        await self.config.set_guild(guild_config)
        
    @guild_config.command(
        name="mod-roles",
        options=[
            Option(
                str,
                name="action",
                choices=[
                    OptionChoice(name="Add role", value="append"),
                    OptionChoice(name="Remove role", value="unappend"),
                    OptionChoice(name="View roles", value="view"),
                ],
            ),
            Option(
                Role,
                name="role",
                required=False,
            ),
        ],
        checks=[check_member_privilage],
    )
    async def guild_config__mod_roles(
        self, ctx: ApplicationContext, action: str, role: Role | None = None
    ):
        if action != "view" and role is None:
            await ctx.send(
                error(
                    "If you are appending/unappending to the mod role list, you must include a role to parameter."
                )
            )
            return

        await ctx.defer()

        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)

        role_list: List[Role] = guild_config.mod_role_ids or []

        if action == "view":
            message = "The following roles are considered mods:\n{}"
            set_of_roles = {
                f"{ctx.guild.get_role(role_id).name or ''} ({role_id})" for role_id in role_list
            }
            await ctx.followup.send(info(message.format(", ".join(set_of_roles))))
        elif action == "append":
            if role.id not in role_list:
                role_list.append(role.id)

            message = "{} was appended to the list. The list is now: {}"
            set_of_roles = {
                f"{ctx.guild.get_role(role_id).name or ''} ({role_id})" for role_id in role_list
            }
            await ctx.followup.send(success(message.format(role, ", ".join(set_of_roles))))
        elif action == "unappend":
            while role.id in role_list:
                role_list.remove(role.id)

            message = "{} was removed from the list. The list is now: {}"
            set_of_roles = {
                f"{ctx.guild.get_role(role_id).name or ''} ({role_id})" for role_id in role_list
            }
            await ctx.followup.send(success(message.format(role, ", ".join(set_of_roles))))

        guild_config.mod_role_ids = list(set(role_list))
        await self.config.set_guild(guild_config)

    @guild_config.command(name="mystic-role", checks=[check_member_privilage])
    async def guild_config__mystic_role(self, ctx: ApplicationContext, value: Role) -> None:
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        guild_config.mystic_role = value.id
        await self.config.set_guild(guild_config)

        await send(
            ctx,
            f"Set `mystic_role` to `{value.mention}`.",
            ephemeral=True,
        )

    @guild_config.command(name="valor-role", checks=[check_member_privilage])
    async def guild_config__valor_role(self, ctx: ApplicationContext, value: Role) -> None:
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        guild_config.valor_role = value.id
        await self.config.set_guild(guild_config)

        await send(
            ctx,
            f"Set `valor_role` to `{value.mention}`.",
            ephemeral=True,
        )

    @guild_config.command(name="instinct-role", checks=[check_member_privilage])
    async def guild_config__instinct_role(self, ctx: ApplicationContext, value: Role) -> None:
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        guild_config.instinct_role = value.id
        await self.config.set_guild(guild_config)

        await send(
            ctx,
            f"Set `instinct_role` to `{value.mention}`.",
            ephemeral=True,
        )

    @guild_config.command(name="tl40-role", checks=[check_member_privilage])
    async def guild_config__tl40_role(self, ctx: ApplicationContext, value: Role) -> None:
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        guild_config.tl40_role = value.id
        await self.config.set_guild(guild_config)

        await send(
            ctx,
            f"Set `tl40_role` to `{value.mention}`.",
            ephemeral=True,
        )

    # @guild_config.command(name="introduction-note", checks=[check_member_privilage])
    # async def guild_config__introduction_note(self, ctx: ApplicationContext, value: str) -> None:
    #     """Send a note to a member upon running `profile create` (aka, `approve`)

    #     Set value to `None` to empty it
    #     """
    #     guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
    #     if value.lower() == "none":
    #         value = None
    #     guild_config.introduction_note = value
    #     await self.config.set_guild(guild_config)

    #     if value is None:
    #         await send(
    #             ctx,
    #             "Unset `introduction_note`.",
    #             ephemeral=True,
    #         )
    #     else:
    #         await send(
    #             ctx,
    #             f"Set `introduction_note` to `{value}`.",
    #             ephemeral=True,
    #         )

    # @_set_global.command(name="notice", checks=[is_owner])
    # async def set__notice(self, ctx: ApplicationContext, value: str) -> None:
    #     global_config: GlobalConfig = await self.config.get_global()
    #     if value.lower() == "none":
    #         value = GlobalConfig.notice
    #     global_config.notice = value
    #     await self.config.set_global(GlobalConfig)

    #     await send(
    #         ctx,
    #         f"Set `notice` to `{value}`.",
    #         ephemeral=True,
    #     )

    # @_set_global.command(name="footer", checks=[is_owner])
    # async def set__footer(self, ctx: ApplicationContext, value: str) -> None:
    #     global_config: GlobalConfig = await self.config.get_global()
    #     if value.lower() == "none":
    #         value = GlobalConfig.embed_footer
    #     global_config.embed_footer = value
    #     await self.config.set_global(GlobalConfig)

    #     await send(
    #         ctx,
    #         f"Set `embed_footer` to `{value}`.",
    #         ephemeral=True,
    #     )
