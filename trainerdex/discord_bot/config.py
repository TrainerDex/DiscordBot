from __future__ import annotations

import logging
import os
from dataclasses import asdict
from enum import Enum
from typing import TYPE_CHECKING, AsyncIterator, Mapping, MutableMapping, Union

from discord import Guild, Member, TextChannel, User
from motor.motor_asyncio import AsyncIOMotorClient as MotorClient
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from pymongo.database import Database

from trainerdex.discord_bot.datatypes import (
    ChannelConfig,
    GlobalConfig,
    GuildConfig,
    MemberConfig,
    ModuleMeta,
    UserConfig,
)

if TYPE_CHECKING:
    from trainerdex.discord_bot.modules.base import Module


class StaticDocuments(Enum):
    GLOBAL_CONFIG = 0
    _ = 1


JSONObject = Union[None, int, str, bool, list["JSONObject"], dict[str, "JSONObject"]]

logger: logging.Logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        logger.info("Initializing Config Client...")
        self.mongo: MotorClient = MotorClient(os.environ.get("MONGODB_URI", "mongodb://tdx:tdx@mongo:27017/"))
        self.database: Database = self.mongo[os.environ.get("MONGODB_NAME", "trainerdex")]

    def _get_collection(self, collection: str) -> Collection:
        return self.database[collection]

    async def get_global(self, *, create: bool = True) -> GlobalConfig:
        return GlobalConfig()

    async def get_module_metadata(self, module: Module | type[Module], create: bool = True) -> ModuleMeta:
        from trainerdex.discord_bot.modules.base import Module

        if isinstance(module, Module):
            module: type[Module] = module.__class__
        elif not issubclass(module, Module):
            raise ValueError("module must be a subclass of Module.")

        data: MutableMapping = await self._get_collection("cogs").find_one({"_id": module.METADATA_ID})

        if data is None and create:
            document: ModuleMeta = ModuleMeta(_id=module.METADATA_ID, enabled=True, last_loaded=None)
            self._get_collection("cogs").insert_one(asdict(document))
            data: MutableMapping = await self._get_collection("cogs").find_one({"_id": module.METADATA_ID})
        elif data is None and not create:
            raise ValueError("No entry found.")
        return ModuleMeta.from_mapping(data)

    async def get_many_module_metadata(self, filter: Mapping = None) -> AsyncIterator[ModuleMeta]:
        curser: Cursor = self._get_collection("cogs").find(filter)
        async for document in curser:
            yield ModuleMeta.from_mapping(document)

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

    async def get_channel(self, channel: TextChannel | int, *, create: bool = True) -> ChannelConfig:
        if isinstance(channel, TextChannel):
            channel = channel.id
        data: MutableMapping = await self._get_collection("channels").find_one({"_id": channel})

        if data is None and create:
            document: ChannelConfig = ChannelConfig(_id=channel)
            self._get_collection("channels").insert_one(asdict(document))
            data: MutableMapping = await self._get_collection("channels").find_one({"_id": channel})
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
        pass

    async def set_module_metadata(self, document: ModuleMeta):
        data: MutableMapping = asdict(document)
        await self._get_collection("cogs").update_one({"_id": document._id}, {"$set": data}, upsert=True)

    async def set_guild(self, document: GuildConfig):
        data: MutableMapping = asdict(document)
        await self._get_collection("guilds").update_one({"_id": document._id}, {"$set": data}, upsert=True)

    async def set_channel(self, document: ChannelConfig):
        data: MutableMapping = asdict(document)
        await self._get_collection("channels").update_one({"_id": document._id}, {"$set": data}, upsert=True)

    async def set_user(self, document: UserConfig):
        data: MutableMapping = asdict(document)
        await self._get_collection("users").update_one({"_id": document._id}, {"$set": data}, upsert=True)

    async def set_member(self, document: MemberConfig):
        data: MutableMapping = asdict(document)
        await self._get_collection("members").update_one(
            {"user_id": document.user_id, "guild_id": document.guild_id},
            {"$set": data},
            upsert=True,
        )
