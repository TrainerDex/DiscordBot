import json
from typing import Mapping

from discord import ApplicationContext, Attachment, SlashCommandGroup

from trainerdex_discord_bot.checks import is_owner
from trainerdex_discord_bot.cogs.interface import Cog
from trainerdex_discord_bot.config import TokenDocuments
from trainerdex_discord_bot.constants import ADMIN_GUILD_ID
from trainerdex_discord_bot.utils.chat_formatting import error
from trainerdex_discord_bot.utils.general import send


class Admin(Cog):
    _token = SlashCommandGroup("token", "Set tokens for the bot.")

    @_token.command(
        name="google_cloud",
        description="Sets an application token via a .json file",
        default_permission=False,
        checks=[is_owner],
        guild_ids=[ADMIN_GUILD_ID],
    )
    async def set_google_cloud_token(self, ctx: ApplicationContext, token_file: Attachment):
        try:
            token: Mapping = json.loads(await token_file.read())
        except (json.JSONDecodeError, TypeError) as e:
            send(ctx, error(f"Failed to parse token file: {e}"))
            return

        await self.config.set_token(TokenDocuments.GOOGLE.value, token)
        await send(ctx, "Set Google Cloud token.", ephemeral=True)
