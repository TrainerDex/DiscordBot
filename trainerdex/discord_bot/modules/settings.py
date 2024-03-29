from typing import TYPE_CHECKING, List
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from discord import ApplicationContext, Option, OptionChoice, Permissions, SlashCommandGroup, TextChannel
from discord.role import Role

from trainerdex.discord_bot.checks import check_member_privilage
from trainerdex.discord_bot.modules.base import Module
from trainerdex.discord_bot.utils.chat_formatting import error, info, success

if TYPE_CHECKING:
    from trainerdex.discord_bot.datatypes import GuildConfig


class SettingsModule(Module):
    @classmethod
    @property
    def METADATA_ID(cls) -> str:
        return "SettingsCog"

    guild_config = SlashCommandGroup(
        "server-config",
        "Set server settings",
        checks=[check_member_privilage],
        default_member_permissions=Permissions(0x20),
    )

    @guild_config.command(name="assign-roles-on-join", checks=[check_member_privilage])
    async def guild_config__assign_roles_on_join(self, ctx: ApplicationContext, value: bool) -> None:
        """Modify the roles of members when they're approved.

        This is useful for granting users access to the rest of the server.
        """
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        guild_config.assign_roles_on_join = value
        await self.config.set_guild(guild_config)

        await ctx.respond(
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

        await ctx.respond(
            f"Set `set_nickname_on_join` to `{value}`.",
            ephemeral=True,
        )

    @guild_config.command(name="set-nickname-on-update", checks=[check_member_privilage])
    async def guild_config__set_nickname_on_update(self, ctx: ApplicationContext, value: bool) -> None:
        """Modify the nickname of members when they update their Total XP.

        This is useful for setting levels in their name.
        """
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        guild_config.set_nickname_on_update = value
        await self.config.set_guild(guild_config)

        await ctx.respond(
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
            await ctx.respond(
                error(
                    "If you are appending/unappending to the grant/revoke lists, you must include a role to parameter."
                )
            )
            return

        await ctx.interaction.response.defer()
        ctx.interaction.response._responded = True

        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)

        if array == "grant":
            role_list: List[Role] = guild_config.roles_to_assign_on_approval.add or []
        elif array == "revoke":
            role_list: List[Role] = guild_config.roles_to_assign_on_approval.remove or []
        else:
            raise ValueError()

        if action == "append":
            if role.id not in role_list:
                role_list.append(role.id)

            message = "{} was appended to the list. The list is now: {}"
            set_of_roles = {f"{ctx.guild.get_role(role_id).name or ''} ({role_id})" for role_id in role_list}
            await ctx.respond(success(message.format(role, ", ".join(set_of_roles))))
        elif action == "unappend":
            while role.id in role_list:
                role_list.remove(role.id)

            set_of_roles = {f"{ctx.guild.get_role(role_id).name or ''} ({role_id})" for role_id in role_list}
            message = "{} was removed from the list. The list is now: {}"
            await ctx.respond(success(message.format(role, ", ".join(set_of_roles))))

        elif action == "view":
            set_of_roles = {f"{ctx.guild.get_role(role_id).name or ''} ({role_id})" for role_id in role_list}
            message = (
                "The following roles will be modified for a user when they are granted access to the guild:\n{}"
            )
            await ctx.respond(info(message.format(", ".join(set_of_roles))))
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
    async def guild_config__mod_roles(self, ctx: ApplicationContext, action: str, role: Role | None = None):
        if action != "view" and role is None:
            await ctx.respond(
                error("If you are appending/unappending to the mod role list, you must include a role to parameter.")
            )
            return

        await ctx.interaction.response.defer()
        ctx.interaction.response._responded = True

        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)

        role_list: List[Role] = guild_config.mod_role_ids or []

        if action == "append":
            if role.id not in role_list:
                role_list.append(role.id)

            message = "{} was appended to the list. The list is now: {}"
            set_of_roles = {f"{ctx.guild.get_role(role_id).name or ''} ({role_id})" for role_id in role_list}
            await ctx.respond(success(message.format(role, ", ".join(set_of_roles))))
        elif action == "unappend":
            while role.id in role_list:
                role_list.remove(role.id)

            set_of_roles = {f"{ctx.guild.get_role(role_id).name or ''} ({role_id})" for role_id in role_list}
            message = "{} was removed from the list. The list is now: {}"
            await ctx.respond(success(message.format(role, ", ".join(set_of_roles))))

        elif action == "view":
            set_of_roles = {f"{ctx.guild.get_role(role_id).name or ''} ({role_id})" for role_id in role_list}
            message = "The following roles are considered mods:\n{}"
            await ctx.respond(info(message.format(", ".join(set_of_roles))))
        guild_config.mod_role_ids = list(set(role_list))
        await self.config.set_guild(guild_config)

    @guild_config.command(name="mystic-role", checks=[check_member_privilage])
    async def guild_config__mystic_role(self, ctx: ApplicationContext, value: Role) -> None:
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        guild_config.mystic_role = value.id
        await self.config.set_guild(guild_config)

        await ctx.respond(
            f"Set `mystic_role` to `{value.mention}`.",
            ephemeral=True,
        )

    @guild_config.command(name="valor-role", checks=[check_member_privilage])
    async def guild_config__valor_role(self, ctx: ApplicationContext, value: Role) -> None:
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        guild_config.valor_role = value.id
        await self.config.set_guild(guild_config)

        await ctx.respond(
            f"Set `valor_role` to `{value.mention}`.",
            ephemeral=True,
        )

    @guild_config.command(name="instinct-role", checks=[check_member_privilage])
    async def guild_config__instinct_role(self, ctx: ApplicationContext, value: Role) -> None:
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        guild_config.instinct_role = value.id
        await self.config.set_guild(guild_config)

        await ctx.respond(
            f"Set `instinct_role` to `{value.mention}`.",
            ephemeral=True,
        )

    @guild_config.command(name="tl40-role", checks=[check_member_privilage])
    async def guild_config__tl40_role(self, ctx: ApplicationContext, value: Role) -> None:
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        guild_config.tl40_role = value.id
        await self.config.set_guild(guild_config)

        await ctx.respond(
            f"Set `tl40_role` to {value.mention}.",
            ephemeral=True,
        )

    @guild_config.command(name="timezone", checks=[check_member_privilage])
    async def guild_config__timezone(self, ctx: ApplicationContext, value: str) -> None:
        """Set the timezone for the server. This is used for the weekly leaderboard."""
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)

        try:
            ZoneInfo(value.strip())
        except ZoneInfoNotFoundError:
            await ctx.respond(
                f"Cannot set `timezone` to `{value}`. For a list of valid timezones, please check this table: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List ",
                ephemeral=True,
            )
            return

        guild_config.timezone = value.strip()
        await self.config.set_guild(guild_config)

        await ctx.respond(
            f"Set `timezone` to `{value}`.",
            ephemeral=True,
        )

    @guild_config.command(name="leaderboard-channel", checks=[check_member_privilage])
    async def guild_config__leaderboard_channel(self, ctx: ApplicationContext, value: TextChannel) -> None:
        """Set a channel for the bot to post weekly leaderboard messages to."""
        perms = value.permissions_for(ctx.me)

        if not (perms.send_messages and perms.create_public_threads and perms.send_messages_in_threads):
            await ctx.respond(
                "The channel must be able to be messaged and be able to create public threads. Leaderboard may not post.",
                ephemeral=True,
            )
            return

        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)

        guild_config.leaderboard_channel_id = value.id
        await self.config.set_guild(guild_config)

        await ctx.respond(
            f"Set `leaderboard_channel` to {value.mention}.",
            ephemeral=True,
        )

    @guild_config.command(name="enable-weekly-leaderboard", checks=[check_member_privilage])
    async def guild_config__post_weekly_leaderboards(self, ctx: ApplicationContext, value: bool) -> None:
        """Post leaderboards weekly on Monday 12:00 local. (Timezone is set in the config, default is UTC)"""
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        guild_config.post_weekly_leaderboards = value
        await self.config.set_guild(guild_config)

        await ctx.respond(
            f"Set `post_weekly_leaderboards` to `{value}`.",
            ephemeral=True,
        )
