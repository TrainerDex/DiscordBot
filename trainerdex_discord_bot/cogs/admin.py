import json
from typing import TYPE_CHECKING, AsyncIterator, Mapping

from discord import ApplicationContext, Attachment, SlashCommandGroup
from discord.commands import permissions
from prettytable import PrettyTable

from trainerdex_discord_bot.checks import is_owner
from trainerdex_discord_bot.cogs.interface import Cog
from trainerdex_discord_bot.config import TokenDocuments
from trainerdex_discord_bot.constants import ADMIN_GUILD_ID
from trainerdex_discord_bot.utils.chat_formatting import (
    bool_to_emoji,
    code,
    error,
    italics,
)
from trainerdex_discord_bot.utils.general import send

if TYPE_CHECKING:
    from trainerdex_discord_bot.datatypes import CogMeta


class Admin(Cog):
    _cog_control = SlashCommandGroup("cogs", "Control the bot's cogs.", checks=[is_owner])

    @_cog_control.command(
        name="enable",
        default_permission=False,
        checks=[is_owner],
        guild_ids=[ADMIN_GUILD_ID],
    )
    @permissions.is_owner()
    async def enable_cog(self, ctx: ApplicationContext, cog: str, start_now: bool = True) -> None:
        """Enable a cog to start on load of the bot. Also starts the cog if it is already loaded."""
        from trainerdex_discord_bot import cogs

        cog_class: type[Cog] = getattr(cogs, cog, None)

        if cog_class is None:
            await send(
                ctx,
                error(
                    f"Cog {italics(cog)} does not exist. Please check your spelling and try again."
                ),
            )
            return

        cog_meta: CogMeta = await self.config.get_cog_meta(cog_class)
        cog_meta.enabled = True
        await self.config.set_cog_meta(cog_meta)

        await send(ctx, f"Enabled {italics(cog)}.")

        if start_now:
            self.bot.add_cog(cog_class(self._common))

    @_cog_control.command(
        name="start",
        default_permission=False,
        checks=[is_owner],
        guild_ids=[ADMIN_GUILD_ID],
    )
    @permissions.is_owner()
    async def start_cog(self, ctx: ApplicationContext, cog: str) -> None:
        """Attempt to start a cog."""
        from trainerdex_discord_bot import cogs

        cog_class: type[Cog] = getattr(cogs, cog, None)

        if cog_class is None:
            await send(
                ctx,
                error(
                    f"Cog {italics(cog)} does not exist. Please check your spelling and try again."
                ),
            )
            return

        self.bot.add_cog(cog_class(self._common))
        await send(ctx, f"Started {italics(cog)}.")

    @_cog_control.command(
        name="disable",
        default_permission=False,
        checks=[is_owner],
        guild_ids=[ADMIN_GUILD_ID],
    )
    @permissions.is_owner()
    async def disable_cog(self, ctx: ApplicationContext, cog: str, stop_cog: bool = True) -> None:
        """Disable a cog from being loaded."""
        from trainerdex_discord_bot import cogs

        cog_class: type[Cog] = getattr(cogs, cog, None)

        if cog_class is None:
            await send(
                ctx,
                error(
                    f"Cog {italics(cog)} does not exist. Please check your spelling and try again."
                ),
            )
            return

        cog_meta: CogMeta = await self.config.get_cog_meta(cog_class)
        cog_meta.enabled = False
        await self.config.set_cog_meta(cog_meta)

        await send(ctx, f"Disabled {italics(cog)}.")

        if stop_cog:
            self.bot.remove_cog(cog_class.__name__)
            await send(ctx, f"Stopped {italics(cog)}.")

    @_cog_control.command(
        name="stop",
        default_permission=False,
        checks=[is_owner],
        guild_ids=[ADMIN_GUILD_ID],
    )
    @permissions.is_owner()
    async def stop_cog(self, ctx: ApplicationContext, cog: str) -> None:
        """Stops a cog."""
        from trainerdex_discord_bot import cogs

        cog_class: type[Cog] = getattr(cogs, cog, None)

        if cog_class is None:
            await send(
                ctx,
                error(
                    f"Cog {italics(cog)} does not exist. Please check your spelling and try again."
                ),
            )
            return

        self.bot.remove_cog(cog_class.__name__)
        await send(ctx, f"Stopped {italics(cog)}.")

    @_cog_control.command(
        name="list",
        default_permission=False,
        checks=[is_owner],
        guild_ids=[ADMIN_GUILD_ID],
    )
    @permissions.is_owner()
    async def list_cogs(self, ctx: ApplicationContext) -> None:
        """List all cogs."""
        from trainerdex_discord_bot import cogs

        cog_mapping: AsyncIterator[CogMeta] = self.config.get_many_cog_meta()

        output = PrettyTable(["Name", "Enabled", "Loaded"])

        async for cog in cog_mapping:
            cog_class: type[Cog] = getattr(cogs, cog.cog_name, None)
            if cog_class is not None:
                loaded = bool(self.bot.cogs.get(cog.cog_name) is not None)
                output.add_row([cog.cog_name, bool_to_emoji(cog.enabled), bool_to_emoji(loaded)])

        await send(ctx, f"Cogs: {code(output.get_string())}")

    _token = SlashCommandGroup("token", "Set tokens for the bot.")

    @_token.command(
        name="google_cloud",
        description="Sets an application token via a .json file",
        default_permission=False,
        checks=[is_owner],
        guild_ids=[ADMIN_GUILD_ID],
    )
    @permissions.is_owner()
    async def set_google_cloud_token(self, ctx: ApplicationContext, token_file: Attachment):
        try:
            token: Mapping = json.loads(await token_file.read())
        except (json.JSONDecodeError, TypeError) as e:
            send(ctx, error(f"Failed to parse token file: {e}"))
            return

        await self.config.set_token(TokenDocuments.GOOGLE.value, token)
        await send(ctx, "Set Google Cloud token.", ephemeral=True)
