from typing import TYPE_CHECKING

from discord import ApplicationContext, Permissions, SlashCommandGroup
from discord.commands import permissions
from discord.role import Role

from trainerdex_discord_bot.checks import has_permissions, is_owner
from trainerdex_discord_bot.cogs.interface import Cog
from trainerdex_discord_bot.datatypes import GlobalConfig
from trainerdex_discord_bot.utils.general import send

if TYPE_CHECKING:
    from trainerdex_discord_bot.datatypes import GuildConfig


class SettingsCog(Cog):
    _set_guild = SlashCommandGroup(
        "guild-config",
        "Set guild settings",
        checks=[has_permissions(Permissions(0x20))],
    )
    _set_channel = SlashCommandGroup(
        "channel-config",
        "Set channel settings",
        checks=[has_permissions(Permissions(0x10))],
    )
    _set_global = SlashCommandGroup(
        "global-config",
        "Set global settings",
        checks=[is_owner],
    )

    @_set_guild.command(name="assign-roles-on-join", checks=[has_permissions(Permissions(0x20))])
    async def set__guild__assign_roles_on_join(self, ctx: ApplicationContext, value: bool) -> None:
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

    @_set_guild.command(name="set-nickname-on-join", checks=[has_permissions(Permissions(0x20))])
    async def set__guild__set_nickname_on_join(self, ctx: ApplicationContext, value: bool) -> None:
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

    @_set_guild.command(name="set-nickname-on-update", checks=[has_permissions(Permissions(0x20))])
    async def set__guild__set_nickname_on_update(
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

    # @_set_guild.command(name="roles-to-assign-on-approval", checks=[has_permissions(Permissions(0x20))])
    # async def set__guild__roles_to_assign_on_approval(
    #     self,
    #     ctx: ApplicationContext,
    #     action: Optional[Literal["add", "remove"]] = None,
    #     roles: Optional[Role] = None,
    # ) -> None:
    #     """Which roles to add/remove to a user on approval

    #     Usage:
    #         [p]set guild roles_to_assign_on_approval add @Verified, @Trainer ...
    #             Assign these roles to users when they are approved
    #         [p]set guild roles_to_assign_on_approval remove @Guest
    #             Remove these roles from users when they are approved
    #     """
    #     guild_config: GuildConfig = await self.config.get_guild(ctx.guild)

    #     if action == "add":
    #         if roles:
    #             guild_config.roles_to_assign_on_approval.add = [
    #                 x.id for x in ctx.message.role_mentions
    #             ]
    #             await self.config.set_guild(guild_config)
    #     elif action == "remove":
    #         if roles:
    #             guild_config.roles_to_assign_on_approval.remove = [
    #                 x.id for x in ctx.message.role_mentions
    #             ]
    #             await self.config.set_guild(guild_config)
    #     await send(ctx, f"{guild_config.roles_to_assign_on_approval=}")

    @_set_guild.command(name="mystic-role", checks=[has_permissions(Permissions(0x20))])
    async def set__guild__mystic_role(self, ctx: ApplicationContext, value: Role) -> None:
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        guild_config.mystic_role = value.id
        await self.config.set_guild(guild_config)

        await send(
            ctx,
            f"Set `mystic_role` to `{value.mention}`.",
            ephemeral=True,
        )

    @_set_guild.command(name="valor-role", checks=[has_permissions(Permissions(0x20))])
    async def set__guild__valor_role(self, ctx: ApplicationContext, value: Role) -> None:
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        guild_config.valor_role = value.id
        await self.config.set_guild(guild_config)

        await send(
            ctx,
            f"Set `valor_role` to `{value.mention}`.",
            ephemeral=True,
        )

    @_set_guild.command(name="instinct-role", checks=[has_permissions(Permissions(0x20))])
    async def set__guild__instinct_role(self, ctx: ApplicationContext, value: Role) -> None:
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        guild_config.instinct_role = value.id
        await self.config.set_guild(guild_config)

        await send(
            ctx,
            f"Set `instinct_role` to `{value.mention}`.",
            ephemeral=True,
        )

    @_set_guild.command(name="tl40-role", checks=[has_permissions(Permissions(0x20))])
    async def set__guild__tl40_role(self, ctx: ApplicationContext, value: Role) -> None:
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        guild_config.tl40_role = value.id
        await self.config.set_guild(guild_config)

        await send(
            ctx,
            f"Set `tl40_role` to `{value.mention}`.",
            ephemeral=True,
        )

    @_set_guild.command(name="introduction-note", checks=[has_permissions(Permissions(0x20))])
    async def set__guild__introduction_note(self, ctx: ApplicationContext, value: str) -> None:
        """Send a note to a member upon running `profile create` (aka, `approve`)

        Set value to `None` to empty it
        """
        guild_config: GuildConfig = await self.config.get_guild(ctx.guild)
        if value.lower() == "none":
            value = None
        guild_config.introduction_note = value
        await self.config.set_guild(guild_config)

        if value is None:
            await send(
                ctx,
                "Unset `introduction_note`.",
                ephemeral=True,
            )
        else:
            await send(
                ctx,
                f"Set `introduction_note` to `{value}`.",
                ephemeral=True,
            )

    @_set_global.command(name="notice", checks=[is_owner])
    async def set__notice(self, ctx: ApplicationContext, value: str) -> None:
        global_config: GlobalConfig = await self.config.get_global()
        if value.lower() == "none":
            value = GlobalConfig.notice
        global_config.notice = value
        await self.config.set_global(GlobalConfig)

        await send(
            ctx,
            f"Set `notice` to `{value}`.",
            ephemeral=True,
        )

    @_set_global.command(name="footer", checks=[is_owner])
    async def set__footer(self, ctx: ApplicationContext, value: str) -> None:
        global_config: GlobalConfig = await self.config.get_global()
        if value.lower() == "none":
            value = GlobalConfig.embed_footer
        global_config.embed_footer = value
        await self.config.set_global(GlobalConfig)

        await send(
            ctx,
            f"Set `embed_footer` to `{value}`.",
            ephemeral=True,
        )
