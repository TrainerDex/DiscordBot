import contextlib

from discord import ApplicationContext, Option, OptionChoice, Permissions, SlashCommandGroup, TextChannel
from discord.role import Role

from trainerdex.discord_bot.checks import check_member_privilage
from trainerdex.discord_bot.modules.base import Module
from trainerdex.discord_bot.utils.chat_formatting import error, info, success


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
        guild_config = await self.config.get_guild_v2(ctx.guild)
        if guild_config is None:
            return await ctx.respond("No data found.")

        guild_config.assign_roles_on_join = value
        await self.config.set_guild_v2(guild_config)

        await ctx.respond(
            f"Set `assign_roles_on_join` to `{value}`.",
            ephemeral=True,
        )

    @guild_config.command(name="set-nickname-on-join", checks=[check_member_privilage])
    async def guild_config__set_nickname_on_join(self, ctx: ApplicationContext, value: bool) -> None:
        """Modify the nickname of members when they're approved.

        This is useful for ensuring players can be easily identified.
        """
        guild_config = await self.config.get_guild_v2(ctx.guild)
        if guild_config is None:
            return await ctx.respond("No data found.")

        guild_config.set_nickname_on_join = value
        await self.config.set_guild_v2(guild_config)

        await ctx.respond(
            f"Set `set_nickname_on_join` to `{value}`.",
            ephemeral=True,
        )

    @guild_config.command(name="set-nickname-on-update", checks=[check_member_privilage])
    async def guild_config__set_nickname_on_update(self, ctx: ApplicationContext, value: bool) -> None:
        """Modify the nickname of members when they update their Total XP.

        This is useful for setting levels in their name.
        """
        guild_config = await self.config.get_guild_v2(ctx.guild)
        if guild_config is None:
            return await ctx.respond("No data found.")

        guild_config.set_nickname_on_update = value
        await self.config.set_guild_v2(guild_config)

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
                    OptionChoice(name="Add role", value="add"),
                    OptionChoice(name="Remove role", value="remove"),
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

        guild_config = await self.config.get_guild_v2(ctx.guild)
        if guild_config is None:
            return await ctx.respond("No data found.")

        if array == "grant":
            roles = guild_config.roles_to_append_on_approval
        elif array == "revoke":
            roles = guild_config.roles_to_remove_on_approval
        else:
            raise ValueError()

        if action == "add":
            roles.add(role)

            message = "{} was added to the list. The list is now: {}"
            set_of_roles = {repr(role) for role in roles}
            await ctx.respond(success(message.format(role, ", ".join(set_of_roles))))
        elif action == "remove":
            with contextlib.suppress(KeyError):
                roles.remove(role)

            message = "{} was removed from the list. The list is now: {}"
            set_of_roles = {repr(role) for role in roles}
            await ctx.respond(success(message.format(role, ", ".join(set_of_roles))))

        elif action == "view":
            message = (
                "The following roles will be modified for a user when they are granted access to the guild:\n{}"
            )
            set_of_roles = {repr(role) for role in roles}
            await ctx.respond(info(message.format(", ".join(set_of_roles))))

        if array == "grant":
            guild_config.roles_to_append_on_approval = roles
        elif array == "revoke":
            guild_config.roles_to_remove_on_approval = roles

        await self.config.set_guild_v2(guild_config)

    @guild_config.command(
        name="mod-roles",
        options=[
            Option(
                str,
                name="action",
                choices=[
                    OptionChoice(name="Add role", value="add"),
                    OptionChoice(name="Remove role", value="remove"),
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

        guild_config = await self.config.get_guild_v2(ctx.guild)
        if guild_config is None:
            return await ctx.respond("No data found.")

        if action == "add":
            guild_config.mod_role_ids.add(role)

            message = "{} was appended to the list. The list is now: {}"
            set_of_roles = {repr(role) for role in guild_config.mod_role_ids}
            await ctx.respond(success(message.format(role, ", ".join(set_of_roles))))

        elif action == "remove":
            with contextlib.suppress(KeyError):
                guild_config.mod_role_ids.remove(role)

            set_of_roles = {repr(role) for role in guild_config.mod_role_ids}
            message = "{} was removed from the list. The list is now: {}"
            await ctx.respond(success(message.format(role, ", ".join(set_of_roles))))

        elif action == "view":
            set_of_roles = {repr(role) for role in guild_config.mod_role_ids}
            message = "The following roles are considered mods:\n{}"
            await ctx.respond(info(message.format(", ".join(set_of_roles))))

        await self.config.set_guild_v2(guild_config)

    @guild_config.command(name="mystic-role", checks=[check_member_privilage])
    async def guild_config__mystic_role(self, ctx: ApplicationContext, value: Role) -> None:
        guild_config = await self.config.get_guild_v2(ctx.guild)
        if guild_config is None:
            return await ctx.respond("No data found.")

        guild_config.mystic_role = value
        await self.config.set_guild_v2(guild_config)

        await ctx.respond(
            f"Set `mystic_role` to `{value.mention}`.",
            ephemeral=True,
        )

    @guild_config.command(name="valor-role", checks=[check_member_privilage])
    async def guild_config__valor_role(self, ctx: ApplicationContext, value: Role) -> None:
        guild_config = await self.config.get_guild_v2(ctx.guild)
        if guild_config is None:
            return await ctx.respond("No data found.")

        guild_config.valor_role = value
        await self.config.set_guild_v2(guild_config)

        await ctx.respond(
            f"Set `valor_role` to `{value.mention}`.",
            ephemeral=True,
        )

    @guild_config.command(name="instinct-role", checks=[check_member_privilage])
    async def guild_config__instinct_role(self, ctx: ApplicationContext, value: Role) -> None:
        guild_config = await self.config.get_guild_v2(ctx.guild)
        if guild_config is None:
            return await ctx.respond("No data found.")

        guild_config.instinct_role = value
        await self.config.set_guild_v2(guild_config)

        await ctx.respond(
            f"Set `instinct_role` to `{value.mention}`.",
            ephemeral=True,
        )

    @guild_config.command(name="tl40-role", checks=[check_member_privilage])
    async def guild_config__tl40_role(self, ctx: ApplicationContext, value: Role) -> None:
        guild_config = await self.config.get_guild_v2(ctx.guild)
        if guild_config is None:
            return await ctx.respond("No data found.")

        guild_config.tl40_role = value
        await self.config.set_guild_v2(guild_config)

        await ctx.respond(
            f"Set `tl40_role` to {value.mention}.",
            ephemeral=True,
        )

    @guild_config.command(name="tl50-role", checks=[check_member_privilage])
    async def guild_config__tl50_role(self, ctx: ApplicationContext, value: Role) -> None:
        guild_config = await self.config.get_guild_v2(ctx.guild)
        if guild_config is None:
            return await ctx.respond("No data found.")

        guild_config.tl40_role = value
        await self.config.set_guild_v2(guild_config)

        await ctx.respond(
            f"Set `tl50_role` to {value.mention}.",
            ephemeral=True,
        )

    @guild_config.command(name="timezone", checks=[check_member_privilage])
    async def guild_config__timezone(self, ctx: ApplicationContext, value: str) -> None:
        """Set the timezone for the server. This is used for the weekly leaderboard."""
        guild_config = await self.config.get_guild_v2(ctx.guild)
        if guild_config is None:
            return await ctx.respond("No data found.")

        guild_config.timezone = value
        await self.config.set_guild_v2(guild_config)

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

        guild_config = await self.config.get_guild_v2(ctx.guild)
        if guild_config is None:
            return await ctx.respond("No data found.")

        guild_config.leaderboard_channel = value
        await self.config.set_guild_v2(guild_config)

        await ctx.respond(
            f"Set `leaderboard_channel` to {value.mention}.",
            ephemeral=True,
        )

    @guild_config.command(name="enable-weekly-leaderboard", checks=[check_member_privilage])
    async def guild_config__post_weekly_leaderboards(self, ctx: ApplicationContext, value: bool) -> None:
        """Post leaderboards weekly on Monday 12:00 local. (Timezone is set in the config, default is UTC)"""
        guild_config = await self.config.get_guild_v2(ctx.guild)
        if guild_config is None:
            return await ctx.respond("No data found.")

        guild_config.weekly_leaderboards_enabled = value
        await self.config.set_guild_v2(guild_config)

        await ctx.respond(
            f"Set `post_weekly_leaderboards` to `{value}`.",
            ephemeral=True,
        )
