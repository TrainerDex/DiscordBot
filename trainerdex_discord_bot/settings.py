import json
import logging
from dataclasses import asdict
from typing import Optional, Literal

from discord.message import Message
from discord.role import Role
from discord.ext import commands

from trainerdex_discord_bot.abc import MixinMeta
from trainerdex_discord_bot.datatypes import ChannelConfig, GlobalConfig, GuildConfig
from trainerdex_discord_bot.utils import chat_formatting

logger: logging.Logger = logging.getLogger(__name__)


class Settings(MixinMeta):
    @commands.command(name="quickstart")
    # @checks.mod_or_permissions(manage_guild=True)
    # @checks.bot_in_a_guild()
    async def quickstart(self, ctx: commands.Context) -> None:
        await ctx.message.add_reaction("✅")
        message: Message = await ctx.send("Looking for team roles…")

        guild_config: GuildConfig = self.config.get_guild(ctx.guild)

        try:
            mystic_role: Role = min(
                [x for x in ctx.guild.roles if "Mystic".casefold() in x.name.casefold()]
            )
        except ValueError:
            mystic_role = None
        if mystic_role:
            guild_config.mystic_role = mystic_role.id
            await ctx.send(
                "`{key}` set to {value}".format(key="mystic_role", value=mystic_role),
                delete_after=30,
            )

        try:
            valor_role: Role = min(
                [x for x in ctx.guild.roles if "Valor".casefold() in x.name.casefold()]
            )
        except ValueError:
            valor_role = None
        if valor_role:
            guild_config.valor_role = valor_role.id
            await ctx.send(
                "`{key}` set to {value}".format(key="valor_role", value=valor_role),
                delete_after=30,
            )

        try:
            instinct_role: Role = min(
                [x for x in ctx.guild.roles if "Instinct".casefold() in x.name.casefold()]
            )
        except ValueError:
            instinct_role = None
        if instinct_role:
            guild_config.instinct_role = instinct_role.id
            await ctx.send(
                "`{key}` set to {value}".format(key="instinct_role", value=instinct_role),
                delete_after=30,
            )

        await message.edit(content="Looking for TL40 role…")

        try:
            tl40_role: Role = min(
                [
                    x
                    for x in ctx.guild.roles
                    if ("Level 40".casefold() in x.name.casefold())
                    or ("tl40".casefold() in x.name.casefold())
                ]
            )
        except ValueError:
            tl40_role = None
        if tl40_role:
            guild_config.tl40_role = tl40_role.id
            await ctx.send(
                "`{key}` set to {value}".format(key="tl40_role", value=tl40_role),
                delete_after=30,
            )

        await message.delete(silent=True)

        self.config.set_guild(guild_config)
        output: str = json.dumps(guild_config.__dict__, indent=2, ensure_ascii=False)
        await ctx.send(chat_formatting.box(output, "json"))

    @commands.group(name="tdxset", aliases=["config"], case_insensitive=True)
    async def tdxset(self, ctx: commands.Context) -> None:
        """⬎ Set server and/or channel settings"""
        pass

    @tdxset.group(name="guild", aliases=["server"], case_insensitive=True)
    # @checks.mod_or_permissions(manage_guild=True)
    # @checks.bot_in_a_guild()
    async def tdxset__guild(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            guild_config: GuildConfig = self.config.get_guild(ctx.guild)
            output: str = json.dumps(asdict(guild_config), indent=2, ensure_ascii=False)
            await ctx.send(chat_formatting.box(output, "json"))

    @tdxset__guild.command(name="assign_roles_on_join")
    async def tdxset__guild__assign_roles_on_join(
        self, ctx: commands.Context, value: Optional[bool] = None
    ) -> None:
        """Modify the roles of members when they're approved.

        This is useful for granting users access to the rest of the server.
        """
        guild_config: GuildConfig = self.config.get_guild(ctx.guild)

        if value is not None:
            guild_config.assign_roles_on_join = value
            self.config.set_guild(guild_config)
            await ctx.message.add_reaction("✅")
        await ctx.reply(f"{guild_config.assign_roles_on_join=}")

    @tdxset__guild.command(name="set_nickname_on_join")
    async def tdxset__guild__set_nickname_on_join(
        self, ctx: commands.Context, value: Optional[bool] = None
    ) -> None:
        """Modify the nickname of members when they're approved.

        This is useful for ensuring players can be easily identified.
        """
        guild_config: GuildConfig = self.config.get_guild(ctx.guild)

        if value is not None:
            guild_config.set_nickname_on_join = value
            self.config.set_guild(guild_config)
            await ctx.message.add_reaction("✅")
        await ctx.reply(f"{guild_config.set_nickname_on_join=}")

    # @tdxset__guild.command(name="set_nickname_on_update")
    # async def tdxset__guild__set_nickname_on_update(
    #     self, ctx: commands.Context, value: Optional[bool] = None
    # ) -> None:
    #     """Modify the nickname of members when they update their Total XP.

    #     This is useful for setting levels in their name.
    #     """
    #     guild_config: GuildConfig = self.config.get_guild(ctx.guild)

    #     if value is not None:
    #         guild_config.set_nickname_on_update = value
    #         self.config.set_guild(guild_config)
    #         await ctx.message.add_reaction("✅")
    #     await ctx.reply(f"{guild_config.set_nickname_on_update=}")

    @tdxset__guild.command(name="roles_to_assign_on_approval")
    async def tdxset__guild__roles_to_assign_on_approval(
        self,
        ctx: commands.Context,
        action: Optional[Literal["add", "remove"]] = None,
        roles: Optional[Role] = None,
    ) -> None:
        """Which roles to add/remove to a user on approval

        Usage:
            [p]tdxset guild roles_to_assign_on_approval add @Verified, @Trainer ...
                Assign these roles to users when they are approved
            [p]tdxset guild roles_to_assign_on_approval remove @Guest
                Remove these roles from users when they are approved
        """
        guild_config: GuildConfig = self.config.get_guild(ctx.guild)

        if action == "add":
            if roles:
                guild_config.roles_to_assign_on_approval.add = [
                    x.id for x in ctx.message.role_mentions
                ]
                self.config.set_guild(guild_config)
                await ctx.message.add_reaction("✅")
        elif action == "remove":
            if roles:
                guild_config.roles_to_assign_on_approval.remove = [
                    x.id for x in ctx.message.role_mentions
                ]
                self.config.set_guild(guild_config)
                await ctx.message.add_reaction("✅")
        await ctx.reply(f"{guild_config.roles_to_assign_on_approval=}")

    @tdxset__guild.command(name="mystic_role", aliases=["mystic"])
    async def tdxset__guild__mystic_role(
        self, ctx: commands.Context, value: Optional[Role] = None
    ) -> None:
        guild_config: GuildConfig = self.config.get_guild(ctx.guild)

        if value is not None:
            guild_config.mystic_role = value.id
            self.config.set_guild(guild_config)
            await ctx.message.add_reaction("✅")
        await ctx.reply(f"{guild_config.mystic_role=}")

    @tdxset__guild.command(name="valor_role", aliases=["valor"])
    async def tdxset__guild__valor_role(
        self, ctx: commands.Context, value: Optional[Role] = None
    ) -> None:
        guild_config: GuildConfig = self.config.get_guild(ctx.guild)

        if value is not None:
            guild_config.valor_role = value.id
            self.config.set_guild(guild_config)
            await ctx.message.add_reaction("✅")
        await ctx.reply(f"{guild_config.valor_role=}")

    @tdxset__guild.command(name="instinct_role", aliases=["instinct"])
    async def tdxset__guild__instinct_role(
        self, ctx: commands.Context, value: Optional[Role] = None
    ) -> None:
        guild_config: GuildConfig = self.config.get_guild(ctx.guild)

        if value is not None:
            guild_config.instinct_role = value.id
            self.config.set_guild(guild_config)
            await ctx.message.add_reaction("✅")
        await ctx.reply(f"{guild_config.instinct_role=}")

    @tdxset__guild.command(name="tl40_role", aliases=["tl40"])
    async def tdxset__guild__tl40_role(
        self, ctx: commands.Context, value: Optional[Role] = None
    ) -> None:
        guild_config: GuildConfig = self.config.get_guild(ctx.guild)

        if value is not None:
            guild_config.tl40_role = value.id
            self.config.set_guild(guild_config)
            await ctx.message.add_reaction("✅")
        await ctx.reply(f"{guild_config.tl40_role=}")

    @tdxset__guild.command(name="introduction_note")
    async def tdxset__guild__introduction_note(
        self, ctx: commands.Context, value: Optional[str] = None
    ) -> None:
        """Send a note to a member upon running `profile create` (aka, `approve`)

        Set value to `None` to empty it
        """
        guild_config: GuildConfig = self.config.get_guild(ctx.guild)

        if value is not None:
            if value.lower() == "none":
                value = None
            guild_config.introduction_note = value
            self.config.set_guild(guild_config)
            await ctx.message.add_reaction("✅")
        await ctx.reply(f"{guild_config.introduction_note=}")

    @tdxset.group(name="channel", case_insensitive=True)
    # @checks.mod_or_permissions(manage_guild=True)
    # @checks.bot_in_a_guild()
    async def tdxset__channel(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            channel_config: ChannelConfig = self.config.get_channel(ctx.channel)
            output: str = json.dumps(asdict(channel_config), indent=2, ensure_ascii=False)
            await ctx.send(chat_formatting.box(output, "json"))

    @tdxset__channel.command(name="profile_ocr", aliases=["ocr"])
    async def tdxset__channel__profile_ocr(
        self, ctx: commands.Context, value: Optional[bool] = None
    ) -> None:
        """Set if this channel should accept OCR commands."""
        channel_config: ChannelConfig = self.config.get_channel(ctx.channel)

        if value is not None:
            channel_config.profile_ocr = value
            self.config.set_channel(channel_config)
            await ctx.message.add_reaction("✅")
        await ctx.reply(f"[{ctx.channel.id}] {channel_config.profile_ocr=}")

    @tdxset.command(name="notice")
    # @checks.is_owner()
    async def tdxset__notice(self, ctx: commands.Context, value: Optional[str] = None) -> None:
        global_config: GlobalConfig = self.config.get_global()

        if value is not None:
            if value.lower() == "none":
                value = GlobalConfig.notice
            global_config.notice = value
            self.config.set_global(GlobalConfig)
            await ctx.message.add_reaction("✅")
        await ctx.reply(f"{global_config.notice=}")

    @tdxset.command(name="footer")
    # @checks.is_owner()
    async def tdxset__footer(self, ctx: commands.Context, value: Optional[str] = None) -> None:
        global_config: GlobalConfig = self.config.get_global()

        if value is not None:
            if value.lower() == "none":
                value = GlobalConfig.embed_footer
            global_config.embed_footer = value
            self.config.set_global(GlobalConfig)
            await ctx.message.add_reaction("✅")
        await ctx.reply(f"{global_config.embed_footer=}")