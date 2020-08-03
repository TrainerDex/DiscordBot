import asyncio
from collections import namedtuple
import logging
import signal
import sys
import traceback
from typing import List, Union

import aiohttp

import discord.Guild
from tdx.client.http import HTTPClient
from tdx.client.trainer import Trainer
from tdx.client.user import User
from tdx.client.update import Update
from tdx.client.leaderbard import Leaderboard, GuildLeaderboard

log: logging.Logger = logging.getLogger(__name__)


class Client:
    def __init__(self, token: str = None, loop=None):
        self.loop = asyncio.get_event_loop() if loop is None else loop
        self.http = HTTPClient(token=token, loop=self.loop)
        self._users = ()
        self._trainers = ()

    async def fetch_trainer(self, trainer_id) -> Trainer:
        data = await self.http.get_trainer(trainer_id)
        return Trainer(data=data, conn=self.http)

    async def fetch_trainers(self) -> None:
        data = await self.http.get_trainers(user_id)
        self._trainers = tuple(Trainer(data=x, conn=self.http) for x in data)

    @property
    def trainers(self) -> List[Trainer]:
        return self._trainers

    async def fetch_user(self, user_id) -> User:
        data = await self.http.get_user(user_id)
        return User(data=data, conn=self.http)

    async def fetch_users(self) -> None:
        data = await self.http.get_users(user_id)
        self._users = tuple(User(data=x, conn=self.http) for x in data)

    @property
    def users(self) -> List[User]:
        return self._users

    async def fetch_update(self, update_uuid) -> Update:
        data = await self.http.get_update(update_uuid)
        return Update(data=data, conn=self.http)

    async def fetch_leaderboard(
        self, guild: Union[discord.Guild, int, None] = None
    ) -> Union[GuildLeaderboard, Leaderboard]:
        if isinstance(guild, discord.Guild):
            guild_id = guild.id
            leaderboard_class = GuildLeaderboard
        elif isinstance(guild, int):
            guild_id = guild
            leaderboard_class = GuildLeaderboard
        else:
            leaderboard_class = Leaderboard
        data = await self.http.get_leaderboard(guild_id=guild_id)
        return leaderboard_class(data=data, conn=self.http)

    async def search_trainer(self, nickname: str, refresh_cache: bool = False) -> Trainer:
        """Searches the cache for a trainer that may currently or previous donned a certain nickname

        Parameters
        ----------

            nickname: :class:str
                The nickname of the trainer you want to search for. This search is case insensitive so go wild.

        Returns
        -------

            :class:trainerdex.Trainer

        Raises
        ------

            :class:NotFound

        """

        if refresh_cache:
            await self.fetch_users()
        cached_trainers = self._trainers
        queryset = [x for x in cached_trainers if x.username == nickname]

        if len(queryset) == 1:
            return Trainer(self.client, **response[0])
        else:
            raise NoResultsFoundError
