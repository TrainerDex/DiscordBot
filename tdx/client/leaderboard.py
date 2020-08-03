import datetime
from typing import List

from dateutil.parser import parse, ParserError
from discord.utils import maybe_coroutine
from tdx.converters import TeamConverter
from tdx.models import Faction


class LeaderboardEntry:
    def __init__(self, conn, **kwargs):
        self.http = conn
        self.data = kwargs
        self._trainer = None
        self._faction = None
        self._user = None

    @property
    def level(self) -> int:
        return self.data.get("level", 1)

    @property
    def position(self) -> int:
        return self.data.get("position", None)

    @property
    def trainer_id(self) -> int:
        return self.data.get("id", None)

    @property
    def trainer(self) -> int:
        return self._trainer

    async def get_trainer(self):
        if self._trainer:
            return self._trainer
        raise NotImplementedError
        #
        #
        #
        # self._trainer = trainerdex.Trainer(r.json())
        # return self._trainer

    @property
    def username(self) -> str:
        return self.data.get("username")

    @property
    def faction_id(self) -> int:
        dummy_faction = {"id": 0}
        return self.data.get("faction", dummy_faction).get("id")

    @property
    def faction(self) -> int:
        return self._faction

    async def faction(self) -> Faction:
        if self._faction:
            return self._faction

        self._faction = await TeamConverter().convert(
            None, self.data.get("faction", {"id": 0, "name_en": "No Team"}).get("id")
        )
        return self._faction

    @property
    def total_xp(self) -> int:
        return self.data.get("total_xp")

    @property
    def last_updated(self) -> datetime.datetime:
        try:
            return parse(self.data.get("last_updated"))
        except (TypeError, ParserError):
            return None


class BaseLeaderboard:
    def __init__(self, conn, data):
        self._entries = data
        self.title = None
        self.http = conn
        self.i = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        i = self.i
        if i >= len(self._entries):
            raise StopAsyncIteration
        self.i += 1
        return LeaderboardEntry(self.http, **self._entries[i])

    def __len__(self):
        return len(self._entries)

    def __getitem__(self, key) -> List[LeaderboardEntry]:
        """Retrieves a list of :class:`.LeaderboardEntry` in a position.

        .. note::

            There can be multiple :class:`.LeaderboardEntry` for a position.
            This happens when they both have the same stat.
        """
        return [
            LeaderboardEntry(self.http, **x) for x in self._entries if x.get("position") == key
        ]

    def filter(self, predicate):
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
            xx = LeaderboardEntry(self.http, **x)
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


class Leaderboard(BaseLeaderboard):
    def __init__(self, conn, data):
        super().__init__(conn, data)
        self.title = "Global Leaderboard"


class GuildLeaderboard(BaseLeaderboard):
    def __init__(self, conn, data):
        super().__init__(conn, data)
        self._entries = data.get("leaderboard")
        self.title = data.get("title")
