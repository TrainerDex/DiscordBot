import json
import logging
from typing import Dict, List

import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf


log: logging.Logger = logging.getLogger("red.tdx.settings")
_ = Translator("TrainerDex", __file__)


class Settings(commands.Cog):
    def __init__(self, bot: Red, config: Config) -> None:
        self.bot: Red = bot
        self.config: Config = config

    @commands.group(name="tdxset", aliases=["config"])
    async def settings(self, ctx: commands.Context) -> None:
        pass

    @settings.group(name="guild", aliases=["server"])
    async def settings__guild(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            settings: Dict = await self.config.guild(ctx.guild).all()
            settings: str = json.dumps(settings, indent=2, ensure_ascii=False)
            await ctx.send(cf.box(settings, "json"))

    @settings__guild.command(name="assign_roles_on_join")
    async def settings__guild__assign_roles_on_join(
        self, ctx: commands.Context, value: bool = None
    ) -> None:
        """Modify the roles of members when they're approved.
        
        This is useful for granting users access to the rest of the server.
        """
        if value is not None:
            await self.config.guild(ctx.guild).assign_roles_on_join.set(value)
            await ctx.tick()
            await ctx.send(
                _("`{key}` set to {value}").format(key="guild.assign_roles_on_join", value=value)
            )
        else:
            await ctx.send_help()
            value: bool = await self.config.guild(ctx.guild).assign_roles_on_join()
            await ctx.send(
                _("`{key}` is {value}").format(key="guild.assign_roles_on_join", value=value)
            )

    @settings__guild.command(name="set_nickname_on_join")
    async def settings__guild__set_nickname_on_join(
        self, ctx: commands.Context, value: bool = None
    ) -> None:
        """Modify the nickname of members when they're approved.
        
        This is useful for ensuring players can be easily identified.
        """
        if value is not None:
            await self.config.guild(ctx.guild).set_nickname_on_join.set(value)
            await ctx.tick()
            await ctx.send(
                _("`{key}` set to {value}").format(key="guild.set_nickname_on_join", value=value)
            )
        else:
            await ctx.send_help()
            value: bool = await self.config.guild(ctx.guild).set_nickname_on_join()
            await ctx.send(
                _("`{key}` is {value}").format(key="guild.set_nickname_on_join", value=value)
            )

    @settings__guild.command(name="set_nickname_on_update")
    async def settings__guild__set_nickname_on_update(
        self, ctx: commands.Context, value: bool = None
    ) -> None:
        """Modify the nickname of members when they update their Total XP.
        
        This is useful for setting levels in their name.
        """
        if value is not None:
            await self.config.guild(ctx.guild).set_nickname_on_update.set(value)
            await ctx.tick()
            await ctx.send(
                _("`{key}` set to {value}").format(key="guild.set_nickname_on_update", value=value)
            )
        else:
            await ctx.send_help()
            value: bool = await self.config.guild(ctx.guild).set_nickname_on_update()
            await ctx.send(
                _("`{key}` is {value}").format(key="guild.set_nickname_on_update", value=value)
            )

    @settings__guild.command(name="roles_to_assign_on_approval")
    async def settings__guild__roles_to_assign_on_approval(
        self, ctx: commands.Context, action: str = None, roles: discord.Role = None
    ) -> None:
        """Which roles to add/remove to a user on approval
        
        Usage:
            [p]tdxset guild roles_to_assign_on_approval add @Verified, @Trainer ...
                Assign these roles to users when they are approved
            [p]tdxset guild roles_to_assign_on_approval remove @Guest
                Remove these roles from users when they are approved
        """
        roledict: Dict[str, List[int]] = await self.config.guild(
            ctx.guild
        ).roles_to_assign_on_approval()
        if action == "add":
            if roles:
                roledict["add"]: List[int] = [x.id for x in ctx.message.role_mentions]
                await self.config.guild(ctx.guild).roles_to_assign_on_approval.set(roledict)
                await ctx.tick()
                value: Dict[str, List[int]] = await self.config.guild(
                    ctx.guild
                ).roles_to_assign_on_approval()
                value: str = json.dumps(value, indent=2, ensure_ascii=False)
                await ctx.send(cf.box(value, "json"))
        elif action == "remove":
            if roles:
                roledict["remove"]: List[int] = [x.id for x in ctx.message.role_mentions]
                await self.config.guild(ctx.guild).roles_to_assign_on_approval.set(roledict)
                await ctx.tick()
                value: Dict[str, List[int]] = await self.config.guild(
                    ctx.guild
                ).roles_to_assign_on_approval()
                value: str = json.dumps(value, indent=2, ensure_ascii=False)
                await ctx.send(cf.box(value, "json"))
        else:
            await ctx.send_help()
            value: Dict[str, List[int]] = await self.config.guild(
                ctx.guild
            ).roles_to_assign_on_approval()
            value: str = json.dumps(value, indent=2, ensure_ascii=False)
            await ctx.send(cf.box(value, "json"))

    @settings__guild.command(name="mystic_role")
    async def settings__guild__mystic_role(
        self, ctx: commands.Context, value: discord.Role = None
    ) -> None:
        if value is not None:
            await self.config.guild(ctx.guild).mystic_role.set(value.id)
            await ctx.tick()
            await ctx.send(
                _("`{key}` set to {value}").format(key="guild.mystic_role", value=value)
            )
        else:
            await ctx.send_help()
            value: int = await self.config.guild(ctx.guild).mystic_role()
            await ctx.send(
                _("`{key}` is {value}").format(
                    key="guild.mystic_role", value=ctx.guild.get_role(value)
                )
            )

    @settings__guild.command(name="valor_role")
    async def settings__guild__valor_role(
        self, ctx: commands.Context, value: discord.Role = None
    ) -> None:
        if value is not None:
            await self.config.guild(ctx.guild).valor_role.set(value.id)
            await ctx.tick()
            await ctx.send(_("`{key}` set to {value}").format(key="guild.valor_role", value=value))
        else:
            await ctx.send_help()
            value: int = await self.config.guild(ctx.guild).valor_role()
            await ctx.send(
                _("`{key}` is {value}").format(
                    key="guild.valor_role", value=ctx.guild.get_role(value)
                )
            )

    @settings__guild.command(name="instinct_role")
    async def settings__guild__instinct_role(
        self, ctx: commands.Context, value: discord.Role = None
    ) -> None:
        if value is not None:
            await self.config.guild(ctx.guild).instinct_role.set(value.id)
            await ctx.tick()
            await ctx.send(
                _("`{key}` set to {value}").format(key="guild.instinct_role", value=value)
            )
        else:
            await ctx.send_help()
            value: int = await self.config.guild(ctx.guild).instinct_role()
            await ctx.send(
                _("`{key}` is {value}").format(
                    key="guild.instinct_role", value=ctx.guild.get_role(value)
                )
            )

    @settings__guild.command(name="tl40_role")
    async def settings__guild__tl40_role(
        self, ctx: commands.Context, value: discord.Role = None
    ) -> None:
        if value is not None:
            await self.config.guild(ctx.guild).tl40_role.set(value.id)
            await ctx.tick()
            await ctx.send(_("`{key}` set to {value}").format(key="guild.tl40_role", value=value))
        else:
            await ctx.send_help()
            value: int = await self.config.guild(ctx.guild).tl40_role()
            await ctx.send(
                _("`{key}` is {value}").format(
                    key="guild.tl40_role", value=ctx.guild.get_role(value)
                )
            )

    @settings.group(name="channel")
    async def settings__channel(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            settings: Dict = await self.config.channel(ctx.channel).all()
            settings: str = json.dumps(settings, indent=2, ensure_ascii=False)
            await ctx.send(cf.box(settings, "json"))

    @settings__channel.command(name="profile_ocr")
    async def settings__channel__profile_ocr(
        self, ctx: commands.Context, value: bool = None
    ) -> None:
        """Set if this channel should accept OCR commands."""
        if value is not None:
            await self.config.channel(ctx.channel).profile_ocr.set(value)
            await ctx.tick()
            await ctx.send(
                _("`{key}` set to {value}").format(
                    key=f"channel[{ctx.channel.id}].profile_ocr", value=value
                )
            )
        else:
            await ctx.send_help()
            value: bool = await self.config.channel(ctx.channel).profile_ocr()
            await ctx.send(
                _("`{key}` is {value}").format(
                    key=f"channel[{ctx.channel.id}].profile_ocr", value=value
                )
            )
