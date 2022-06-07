from __future__ import annotations

import logging
import os
from dataclasses import asdict
from enum import Enum
from typing import TYPE_CHECKING, AsyncIterator, Mapping, MutableMapping, Union

from discord import Guild, Member, TextChannel, User
from motor.motor_asyncio import AsyncIOMotorClient as MotorClient
from pymongo.cursor import Cursor

from trainerdex_discord_bot.cogs.interface import Cog
from trainerdex_discord_bot.datatypes import (
    ChannelConfig,
    CogMeta,
    GlobalConfig,
    GuildConfig,
    MemberConfig,
    UserConfig,
)

if TYPE_CHECKING:
    from pymongo.collection import Collection
    from pymongo.database import Database


class StaticDocuments(Enum):
    GLOBAL_CONFIG = 0
    TOKENS = 1


class TokenDocuments(Enum):
    GOOGLE = "google_cloud"
    TRAINERDEX = "trainerdex"


JSONObject = Union[None, int, str, bool, list["JSONObject"], dict[str, "JSONObject"]]

logger: logging.Logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        logger.info("Initializing Config Client...")
        self.mongo: MotorClient = MotorClient(
            os.environ.get("MONGODB_URI", "mongodb://tdx:tdx@mongo:27017/")
        )
        self.database: Database = self.mongo[os.environ.get("MONGODB_NAME", "trainerdex")]

    def _get_collection(self, collection: str) -> Collection:
        return self.database[collection]

    async def get_global(self, *, create: bool = True) -> GlobalConfig:
        data: MutableMapping = await self._get_collection("global").find_one(
            {"_id": StaticDocuments.GLOBAL_CONFIG.value}
        )

        if data is None and create:
            document: GlobalConfig = GlobalConfig(_id=StaticDocuments.GLOBAL_CONFIG.value)
            self._get_collection("global").insert_one(asdict(document))
            data: MutableMapping = await self._get_collection("global").find_one(
                {"_id": StaticDocuments.GLOBAL_CONFIG.value}
            )
        elif data is None and not create:
            raise ValueError("No entry found.")
        return GlobalConfig.from_mapping(data)

    async def get_token(self, service: str) -> Union[JSONObject, None]:
        data: MutableMapping = await self._get_collection("global").find_one(
            {"_id": StaticDocuments.TOKENS.value}
        )

        if data is None:
            return None
        else:
            return data.get(service, None)

    async def get_cog_meta(self, cog: Cog | type[Cog], create: bool = True) -> CogMeta:
        if isinstance(cog, Cog):
            cog: type[Cog] = cog.__class__
        elif not issubclass(cog, Cog):
            raise ValueError("cog must be a subclass of Cog.")

        data: MutableMapping = await self._get_collection("cogs").find_one({"_id": cog.__name__})

        if data is None and create:
            document: CogMeta = CogMeta(_id=cog.__name__, enabled=True, last_loaded=None)
            self._get_collection("cogs").insert_one(asdict(document))
            data: MutableMapping = await self._get_collection("cogs").find_one(
                {"_id": cog.__name__}
            )
        elif data is None and not create:
            raise ValueError("No entry found.")
        return CogMeta.from_mapping(data)

    async def get_many_cog_meta(self, filter: Mapping = None) -> AsyncIterator[CogMeta]:
        curser: Cursor = self._get_collection("cogs").find(filter)
        async for document in curser:
            yield CogMeta.from_mapping(document)

    async def get_guild(self, guild: Guild | int, *, create: bool = True) -> GuildConfig:
        if isinstance(guild, Guild):
            guild = guild.id
        data: MutableMapping = await self._get_collection("guilds").find_one({"_id": guild})

        if data is None and create:
            document: GuildConfig = GuildConfig(_id=guild)
            self._get_collection("guilds").insert_one(asdict(document))
            data: MutableMapping = await self._get_collection("guilds").find_one({"_id": guild})
        elif data is None and not create:
            raise ValueError("No entry found.")
        return GuildConfig.from_mapping(data)

    async def get_channel(
        self, channel: TextChannel | int, *, create: bool = True
    ) -> ChannelConfig:
        if isinstance(channel, TextChannel):
            channel = channel.id
        data: MutableMapping = await self._get_collection("channels").find_one({"_id": channel})

        if data is None and create:
            document: ChannelConfig = ChannelConfig(_id=channel)
            self._get_collection("channels").insert_one(asdict(document))
            data: MutableMapping = await self._get_collection("channels").find_one(
                {"_id": channel}
            )
        elif data is None and not create:
            raise ValueError("No entry found.")
        return ChannelConfig.from_mapping(data)

    async def get_user(self, user: User | int, *, create: bool = True) -> UserConfig:
        if isinstance(user, User):
            user = user.id
        data: MutableMapping = await self._get_collection("users").find_one({"_id": user})

        if data is None and create:
            document: UserConfig = UserConfig(_id=user)
            self._get_collection("users").insert_one(asdict(document))
            data: MutableMapping = await self._get_collection("users").find_one({"_id": user})
        elif data is None and not create:
            raise ValueError("No entry found.")
        return UserConfig.from_mapping(data)

    async def get_member(
        self,
        member_or_user: User | Member | int,
        guild: Guild | int | None = None,
        *,
        create: bool = True,
    ) -> MemberConfig:
        if isinstance(member_or_user, Member):
            user: int = member_or_user.id
            guild: int = member_or_user.guild.id
        elif isinstance(member_or_user, User):
            user: int = user.id
        else:
            user: int = member_or_user

        if not isinstance(member_or_user, Member) and guild is None:
            raise ValueError("Must provide guild when getting user to member config")
        elif isinstance(guild, Guild):
            guild: int = guild.id

        query: Mapping[str, int] = {"user_id": user, "guild_id": guild}
        data: MutableMapping = await self._get_collection("members").find_one(query)

        if data is None and create:
            document: MemberConfig = MemberConfig.create(**query)
            self._get_collection("members").insert_one(asdict(document))
            data: MutableMapping = await self._get_collection("members").find_one(query)
        elif data is None and not create:
            raise ValueError("No entry found.")
        return MemberConfig.from_mapping(data)

    async def set_global(self, document: GlobalConfig):
        data: MutableMapping = asdict(document)
        await self._get_collection("global").update_one(
            {"_id": document._id}, {"$set": data}, upsert=True
        )

    async def set_token(self, service: str, token: JSONObject):
        data: dict[str, JSONObject] = {service: token}
        await self._get_collection("global").update_one(
            {"_id": StaticDocuments.TOKENS.value}, {"$set": data}, upsert=True
        )

    async def set_cog_meta(self, document: CogMeta):
        data: MutableMapping = asdict(document)
        await self._get_collection("cogs").update_one(
            {"_id": document._id}, {"$set": data}, upsert=True
        )

    async def set_guild(self, document: GuildConfig):
        data: MutableMapping = asdict(document)
        await self._get_collection("guilds").update_one(
            {"_id": document._id}, {"$set": data}, upsert=True
        )

    async def set_channel(self, document: ChannelConfig):
        data: MutableMapping = asdict(document)
        await self._get_collection("channels").update_one(
            {"_id": document._id}, {"$set": data}, upsert=True
        )

    async def set_user(self, document: UserConfig):
        data: MutableMapping = asdict(document)
        await self._get_collection("users").update_one(
            {"_id": document._id}, {"$set": data}, upsert=True
        )

    async def set_member(self, document: MemberConfig):
        data: MutableMapping = asdict(document)
        await self._get_collection("members").update_one(
            {"user_id": document.user_id, "guild_id": document.guild_id},
            {"$set": data},
            upsert=True,
        )
