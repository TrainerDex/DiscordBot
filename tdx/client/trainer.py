import re

from dateutil.parser import parse, ParserError

from tdx.client.user import User
from tdx.client.faction import Faction


class Trainer(User):
    def _update(self, data):
        # If data has key '__user_data' it will be the response from the v1 user api, should be jerry rigged into data
        if data.get("__user_data"):
            super()._update(data.get("__user_data"))
        else:
            self.id = int(data.get("owner"))
            self.username = data.get("username")
            self.first_name = None
            self.old_id = int(data.get("id"))

        try:
            self.last_modified = parse(data.get("last_modified"))
        except (TypeError, ParserError):
            self.last_modified = None

        self.nickname = data.get("username")

        try:
            start_date = parse(data.get("start_date"))
        except (TypeError, ParserError):
            self.start_date = None
        else:
            self.start_date = start_date.date()

        self.faction = data.get("faction")
        self.trainer_code = data.get("trainer_code")
        self.is_banned = data.get("is_banned", False)
        self.is_verified = data.get("is_verified")
        self.is_visible = data.get("is_visible")
        self._updates = data.get("updates")

    @property
    def team(self):
        return Faction(self.faction)

    async def edit(self, **options):
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

        if isinstance(options.get("faction"), Faction):
            options["faction"] = options["faction"].id

        if options.get("trainer_code"):
            options["trainer_code"] = re.sub(
                r"\s+", "", str(options["trainer_code"]), flags=re.UNICODE
            )

        new_data = self.http.edit_trainer(self.old_id, **options)
        self._update(new_data)
