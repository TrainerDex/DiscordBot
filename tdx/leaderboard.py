import datetime
from typing import List

import httpx
import trainerdex
from dateutil.parser import parse, ParserError
from discord.utils import maybe_coroutine
from tdx.converters import TeamConverter
from tdx.models import Faction


class LeaderboardEntry:
    async def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        await instance.__init__(*args, **kwargs)
        return instance

    async def __init__(self, **kwargs):
        self.data = kwargs
        self._trainer = None
        self._faction = None
        self._user = None

    @property
    def level(self) -> trainerdex.utils.LevelTuple:
        return trainerdex.utils.level_parser(level=self.data.get("level", 1))

    @property
    def position(self) -> int:
        return self.data.get("position", None)

    @property
    def trainer_id(self) -> int:
        return self.data.get("id", None)

    async def trainer(self) -> trainerdex.Trainer:
        if self._trainer:
            return self._trainer

        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"https://www.trainerdex.co.uk/api/v1/trainers/{self.trainer_id}/"
            )
        print(r.request.method, r.url, r.status_code)
        self._trainer = trainerdex.Trainer(r.json())
        return self._trainer

    @property
    def username(self) -> str:
        return self.data.get("username", None)

    async def faction(self) -> Faction:
        if self._faction:
            return self._faction

        self._faction = await TeamConverter().convert(
            None, self.data.get("faction", {"id": 0, "name_en": "No Team"}).get("id")
        )
        return self._faction

    @property
    def total_xp(self) -> int:
        return self.data.get("total_xp", None)

    xp = total_xp

    @property
    def last_updated(self) -> datetime.datetime:
        try:
            return parse(self.data.get("total_xp", None))
        except (TypeError, ParserError):
            return None

    @property
    def user_id(self) -> int:
        return self.data.get("user_id", None)

    async def user(self) -> trainerdex.User:
        if self._user:
            return self._user

        async with httpx.AsyncClient() as client:
            r = await client.get(f"https://www.trainerdex.co.uk/api/v1/users/{self.trainer_id}/")
        print(r.request.method, r.url, r.status_code)
        self._user = trainerdex.User(r.json())
        return self._user


class Leaderboard:
    async def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        async with httpx.AsyncClient() as client:
            r = await client.get("https://www.trainerdex.co.uk/api/v1/leaderboard/", timeout=60)
        print(r.request.method, r.url, r.status_code)
        limit = kwargs.get("limit", 1000)
        instance.__init__(entries=r.json()[:limit])
        return instance

    def __init__(self, entries):
        self._entries = entries
        self.i = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        i = self.i
        if i >= len(self._entries):
            raise StopAsyncIteration
        self.i += 1
        return await LeaderboardEntry(**self._entries[i])

    async def __getitem__(self, key) -> List[LeaderboardEntry]:
        return [await LeaderboardEntry(**x) for x in self._entries if x.get("position") == key]

    async def filter(self, predicate):
        """Filter the iterable with an (optionally async) predicate.

        Parameters
        ----------
        function: Callable
            A function or coroutine function which takes one item of ``iterable``
            as an argument, and returns ``True`` or ``False``.

        Returns
        -------
            An object which can either be awaited to yield a list of the filtered
            items, or can also act as an async iterator to yield items one by one.

        Examples
        --------
        >>> from tdx.leaderboard import Leaderboard
        >>> def predicate(value):
        ...     return value.faction.id == 0
        >>> iterator = Leaderboard()
        >>> async for i in iterator.filter(predicate):
        ...     print(i)
        

        >>> from redbot.core.utils import AsyncIter
        >>> def predicate(value):
        ...     return value.level.level < 5
        >>> iterator = AsyncIter([1, 10, 5, 100])
        >>> await iterator.filter(predicate)
        [1, 5]

        """
        for x in self._entries:
            xx = await LeaderboardEntry(**x)
            if predicate(xx):
                yield xx

    async def find(self, predicate, default=None):
        """Calls ``predicate`` over items in iterable and return first value to match.

        Parameters
        ----------
        predicate: Union[Callable, Coroutine]
            A function that returns a boolean-like result. The predicate provided can be a coroutine.
        default: Optional[Any]
            The value to return if there are no matches.

        Raises
        ------
        TypeError
            When ``predicate`` is not a callable.

        Examples
        --------
        >>> from tdx.leaderboard import Leaderboard
        >>> await Leaderboard().find(lambda x: x.trainer.id == 1)
        <LeaderboardEntry>
        """
        while True:
            try:
                elem = await self.__anext__()
            except StopAsyncIteration:
                return default
            ret = await maybe_coroutine(predicate, elem)
            if ret:
                return elem
