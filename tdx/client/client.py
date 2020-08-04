import asyncio
import logging
from typing import Iterable, List, Union
from uuid import UUID

from tdx.client.http import HTTPClient
from tdx.client.trainer import Trainer
from tdx.client.user import User
from tdx.client.update import Update
from tdx.client.leaderboard import Leaderboard, GuildLeaderboard
from tdx.client.socialconnection import SocialConnection

log: logging.Logger = logging.getLogger(__name__)


class Client:
    def __init__(self, token: str = None, loop=None) -> None:
        self.loop = asyncio.get_event_loop() if loop is None else loop
        self.http = HTTPClient(token=token, loop=self.loop)

    async def get_trainer(self, trainer_id: int) -> Trainer:
        data = await self.http.get_trainer(trainer_id)
        return Trainer(data=data, conn=self.http)

    async def get_trainers(self) -> Iterable[Trainer]:
        data = await self.http.get_trainers()
        return tuple(Trainer(data=x, conn=self.http) for x in data)

    async def get_user(self, user_id: int) -> User:
        data = await self.http.get_user(user_id)
        return User(data=data, conn=self.http)

    async def get_users(self) -> Iterable[User]:
        data = await self.http.get_users()
        return tuple(User(data=x, conn=self.http) for x in data)

    async def get_update(self, update_uuid: Union[str, UUID]) -> Update:
        data = await self.http.get_update(update_uuid)
        return Update(data=data, conn=self.http)

    async def get_social_connections(
        self, provider: str, uid: Union[str, Iterable[str]]
    ) -> List[SocialConnection]:
        data = await self.http.get_social_connections(provider, uid)
        return [SocialConnection(data=x, conn=self.http) for x in data]

    async def get_leaderboard(self, guild=None) -> Union[GuildLeaderboard, Leaderboard]:
        if guild is not None:
            if isinstance(guild, int):
                guild_id = guild
            else:
                guild_id = guild.id
            leaderboard_class = GuildLeaderboard
        else:
            guild_id = None
            leaderboard_class = Leaderboard
        data = await self.http.get_leaderboard(guild_id=guild_id)
        return leaderboard_class(data=data, conn=self.http)

    async def search_trainer(self, nickname: str) -> Trainer:
        """Searches for a trainer with a certain nickname

        Parameters
        ----------

            nickname: :class:str
                The nickname of the trainer you want to search for.
                This search is case insensitive.

        Returns
        -------

            :class:trainerdex.Trainer

        Raises
        ------

            :class:NotFound

        """

        queryset = self.get_trainers()
        queryset = [x for x in queryset if x.username.casefold() == nickname.casefold()]

        if len(queryset) == 1:
            return Trainer(self.client, **queryset[0])
        else:
            raise IndexError
