from discord import User

from trainerdex.api.client import BaseClient
from trainerdex.api.exceptions import NotFound
from trainerdex.api.socialconnection import SocialConnection
from trainerdex.api.trainer import Trainer
from trainerdex.discord_bot.utils.validators import validate_trainer_nickname


async def get_trainer_from_user(client: BaseClient, user: User, *, prefetch_updates: bool = True) -> Trainer | None:
    """Retrieve a profile from a user's Discord ID.

    This will also fetch updates unless the prefetch_updates argument is set to False.
    """
    social_connections: list[SocialConnection] = await client.get_social_connections(
        "discord",
        [str(user.id)],
    )

    if social_connections:
        trainer: Trainer = await social_connections[0].get_trainer()
        if prefetch_updates:
            await trainer.fetch_updates()
        return trainer


async def get_trainer_from_nickname(
    client: BaseClient, nickname: str, *, prefetch_updates: bool = True
) -> Trainer | None:
    """Retrieve a profile from a Pokémon Go nickname.

    This will also fetch updates unless the prefetch_updates argument is set to False.
    """
    if not validate_trainer_nickname(nickname):
        return None

    try:
        trainer: Trainer = await client.search_trainer(nickname)
    except NotFound:
        return None

    if prefetch_updates:
        await trainer.fetch_updates()
    return trainer


async def get_trainer(
    client: BaseClient,
    *,
    nickname: str | None = None,
    user: User | None = None,
    prefetch_updates: bool = True,
) -> Trainer | None:
    """Retrieve a profile from a Pokémon Go nickname or user's Discord ID

    This will prefer nickname, so if both return a result, the nickname will be used.

    This will also fetch updates unless the prefetch_updates argument is set to False.
    """
    from_nickname = await get_trainer_from_nickname(client, nickname, prefetch_updates=False) if nickname else None
    from_user = await get_trainer_from_user(client, user, prefetch_updates=False) if user else None

    trainer = from_nickname or from_user
    if trainer and prefetch_updates:
        await trainer.fetch_updates()

    return trainer
