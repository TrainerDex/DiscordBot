from typing import Dict, Union, Optional

from tdx.client import abc
from tdx.client.http import HTTPClient
from tdx.client.socialconnection import SocialConnection
from tdx.client.trainer import Trainer


class User(abc.BaseClass):
    def __init__(self, conn: HTTPClient, data: Dict[str, Union[str, int]]) -> None:
        super().__init__(conn, data)
        self._trainer = None

    def _update(self, data: Dict[str, Union[str, int]]) -> None:
        self.id = int(data.get("id"))
        self.username = data.get("username")
        self.first_name = data.get("first_name")
        self.old_id = int(data.get("trainer"))

    async def trainer(self) -> Trainer:
        if self._trainer:
            return self._trainer

        data = await self.http.get_trainer(self.old_id)
        self._trainer = Trainer(data=data, conn=self.http)

        return self._trainer

    async def refresh_from_api(self) -> None:
        data = await self.http.get_user(self.id)
        self._update(data)

    async def add_social_connection(
        self, provider: str, uid: str, extra_data: Optional[Dict] = None
    ) -> SocialConnection:
        data = await self.http.create_social_connection(
            user=self.id, provider=provider, uid=uid, extra_data=extra_data
        )
        return SocialConnection(data=data, conn=self.http)

    async def add_discord(self, discord) -> SocialConnection:
        return await self.add_social_connection("discord", str(discord.id))
