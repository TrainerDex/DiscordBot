import json
import logging
from typing import Dict, List

import discord
from redbot.core import checks, commands, Config
from redbot.core.bot import Red
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf


log: logging.Logger = logging.getLogger("red.tdx.settings")
_ = Translator("TrainerDex", __file__)


class Settings(commands.Cog):
    def __init__(self, bot: Red, config: Config) -> None:
        self.bot: Red = bot
        self.config: Config = config

    @commands.command(name="quickstart")
    @checks.mod_or_permissions(manage_guild=True)
    @checks.bot_in_a_guild()
    async def quickstart(self, ctx: commands.Context) -> None:
        await ctx.tick()
        message = await ctx.send(_("Looking for team roles..."))

        try:
            mystic_role: discord.Role = min(
                [x for x in ctx.guild.roles if _("Mystic").casefold() in x.name.casefold()]
            )
        except ValueError:
            mystic_role = None
        if mystic_role:
            await getattr(self.config.guild(ctx.guild), "mystic_role").set(mystic_role.id)
            await ctx.send(
                _("`{key}` set to {value}").format(key="mystic_role", value=mystic_role),
                delete_after=30,
            )

        try:
            valor_role: discord.Role = min(
                [x for x in ctx.guild.roles if _("Valor").casefold() in x.name.casefold()]
            )
        except ValueError:
            valor_role = None
        if valor_role:
            await getattr(self.config.guild(ctx.guild), "valor_role").set(valor_role.id)
            await ctx.send(
                _("`{key}` set to {value}").format(key="valor_role", value=valor_role),
                delete_after=30,
            )

        try:
            instinct_role: discord.Role = min(
                [x for x in ctx.guild.roles if _("Instinct").casefold() in x.name.casefold()]
            )
        except ValueError:
            instinct_role = None
        if instinct_role:
            await getattr(self.config.guild(ctx.guild), "instinct_role").set(instinct_role.id)
            await ctx.send(
                _("`{key}` set to {value}").format(key="instinct_role", value=instinct_role),
                delete_after=30,
            )

        await message.edit(content=_("Looking for TL40 role..."))

        try:
            tl40_role: discord.Role = min(
                [
                    x
                    for x in ctx.guild.roles
                    if (_("Level 40").casefold() in x.name.casefold())
                    or ("tl40".casefold() in x.name.casefold())
                ]
            )
        except ValueError:
            tl40_role = None
        if tl40_role:
            await getattr(self.config.guild(ctx.guild), "tl40_role").set(tl40_role.id)
            await ctx.send(
                _("`{key}` set to {value}").format(key="tl40_role", value=tl40_role),
                delete_after=30,
            )

        await message.delete()

        settings: Dict = await self.config.guild(ctx.guild).all()
        settings: str = json.dumps(settings, indent=2, ensure_ascii=False)
        await ctx.send(cf.box(settings, "json"))

    @commands.group(name="tdxset", aliases=["config"])
    async def settings(self, ctx: commands.Context) -> None:
        pass

    @settings.group(name="guild", aliases=["server"])
    @checks.mod_or_permissions(manage_guild=True)
    @checks.bot_in_a_guild()
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
                _("`{key}` set to {value}").format(key="guild.assign_roles_on_join", value=value),
                delete_after=30,
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
                _("`{key}` set to {value}").format(key="guild.set_nickname_on_join", value=value),
                delete_after=30,
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
                _("`{key}` set to {value}").format(
                    key="guild.set_nickname_on_update", value=value
                ),
                delete_after=30,
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
                await ctx.send(cf.box(value, "json"), delete_after=30)
        elif action == "remove":
            if roles:
                roledict["remove"]: List[int] = [x.id for x in ctx.message.role_mentions]
                await self.config.guild(ctx.guild).roles_to_assign_on_approval.set(roledict)
                await ctx.tick()
                value: Dict[str, List[int]] = await self.config.guild(
                    ctx.guild
                ).roles_to_assign_on_approval()
                value: str = json.dumps(value, indent=2, ensure_ascii=False)
                await ctx.send(cf.box(value, "json"), delete_after=30)
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
                _("`{key}` set to {value}").format(key="guild.mystic_role", value=value),
                delete_after=30,
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
            await ctx.send(
                _("`{key}` set to {value}").format(key="guild.valor_role", value=value),
                delete_after=30,
            )
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
                _("`{key}` set to {value}").format(key="guild.instinct_role", value=value),
                delete_after=30,
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
            await ctx.send(
                _("`{key}` set to {value}").format(key="guild.tl40_role", value=value),
                delete_after=30,
            )
        else:
            await ctx.send_help()
            value: int = await self.config.guild(ctx.guild).tl40_role()
            await ctx.send(
                _("`{key}` is {value}").format(
                    key="guild.tl40_role", value=ctx.guild.get_role(value)
                )
            )

    @settings.group(name="channel")
    @checks.mod_or_permissions(manage_guild=True)
    @checks.bot_in_a_guild()
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
                ),
                delete_after=30,
            )
        else:
            await ctx.send_help()
            value: bool = await self.config.channel(ctx.channel).profile_ocr()
            await ctx.send(
                _("`{key}` is {value}").format(
                    key=f"channel[{ctx.channel.id}].profile_ocr", value=value
                )
            )

    @settings.group(name="user", aliases=["member"])
    async def settings__user(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            if ctx.guild:
                settings: Dict = {
                    **await self.config.member(ctx.author).all(),
                    **await self.config.user(ctx.author).all(),
                }
            else:
                settings: Dict = await self.config.user(ctx.author).all()
            settings: str = json.dumps(settings, indent=2, ensure_ascii=False)
            await ctx.send(cf.box(settings, "json"))
