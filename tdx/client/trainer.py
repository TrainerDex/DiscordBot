import datetime
import re
from typing import Dict, Union

from dateutil.parser import parse

from tdx.client import abc
from tdx.client.faction import Faction
from tdx.client.update import PartialUpdate, Update
from tdx.client.utils import con

odt = con(parse)


class Trainer(abc.BaseClass):
    def _update(self, data: Dict[str, Union[str, int]]) -> None:
        self.id = int(data.get("owner"))
        self.username = data.get("username")
        self.old_id = int(data.get("id"))
        self.last_modified = odt(data.get("last_modified"))
        self.nickname = data.get("username")
        self.start_date = odt(data.get("start_date")).date() if data.get("start_date") else None
        self.faction = data.get("faction")
        self.trainer_code = data.get("trainer_code")
        self.is_banned = data.get("is_banned", False)
        self.is_verified = data.get("is_verified")
        self.is_visible = data.get("is_visible")
        self._updates = data.get("updates")
        self._user = data.get("_user")

    @property
    def team(self) -> Faction:
        return Faction(self.faction)

    @property
    def updates(self):
        return tuple(PartialUpdate(self.http, x) for x in self._updates)

    async def user(self):
        if self._user:
            return self._user

        # have to import User late to prevent circular imports
        from tdx.client.user import User

        data = await self.http.get_user(self.id)
        self._user = User(data=data, conn=self.http)

        return self._user

    async def refresh_from_api(self) -> None:
        data = await self.http.get_trainer(self._trainer_id)
        self._update(data)

    async def edit(self, **options) -> None:
        """|coro|

        Edits the current trainer

        .. note::
            Changing username is currently unsupported with the current API level.
            Changing IDs is forever unsupported

        Parameters
        -----------
        start_date: :class:`datetime.datetime`
            The date the Trainer started playing Pokemon Go
        faction: Union[:class:`Faction`, :class:`int`]
            The team the Trainer belongs to
        trainer_code: Union[:class:`int`, :class:`int`]
            The Trainer's Trainer/Friend code, this will be processed to remove any whitespace
        is_verified: :class:`bool`
            If the Trainer's information has been looked at and approved.
        is_visible: :class:`bool`
            If the Trainer has given consent for their data to be shared.

        Raises
        ------
        HTTPException
            Editing your profile failed.
        """

        if isinstance(options.get("start_date"), Faction):
            options["start_date"] = options["start_date"].isoformat()

        if isinstance(options.get("faction"), Faction):
            options["faction"] = options["faction"].id

        if options.get("trainer_code"):
            options["trainer_code"] = re.sub(
                r"\s+", "", str(options["trainer_code"]), flags=re.UNICODE
            )

        new_data = self.http.edit_trainer(self.old_id, **options)
        self._update(new_data)

    async def post(self, **options) -> Update:
        """|coro|

        Posts an update on the current trainer

        .. note::
            This will refresh the Trainer instance too
        """
        API_VER = 1
        if API_VER == 1:
            trainer_id = self.old_id
        else:
            trainer_id = self.id

        data = await self.http.create_update(trainer_id, **options)
        result = Update(data=data, conn=self.http)
        await self.refresh_from_api()
        return result
