from __future__ import annotations

import os
from dataclasses import asdict
from typing import TYPE_CHECKING, Mapping, MutableMapping

from discord import Guild, Member, TextChannel, User
from pymongo import MongoClient

from trainerdex_discord_bot.datatypes import (
    ChannelConfig,
    GlobalConfig,
    GuildConfig,
    MemberConfig,
    UserConfig,
)

if TYPE_CHECKING:
    from pymongo.collection import Collection
    from pymongo.database import Database

GLOBAL_CONFIG_ID = 0


class Config:
    def __init__(self):
        self.mongo: MongoClient = MongoClient(os.environ.get("MONGODB_URI"))
        self.database: Database = self.mongo[os.environ.get("MONGODB_NAME")]

    def _get_collection(self, collection: str) -> Collection:
        return self.database[collection]

    def get_global(self, *, create: bool = True) -> GlobalConfig:
        data: MutableMapping = self._get_collection("global").find_one({"_id": GLOBAL_CONFIG_ID})

        if data is None and create:
            document: GlobalConfig = GlobalConfig(_id=GLOBAL_CONFIG_ID)
            self._get_collection("global").insert_one(asdict(document))
            data: MutableMapping = self._get_collection("global").find_one(
                {"_id": GLOBAL_CONFIG_ID}
            )
        elif data is None and not create:
            raise ValueError("No entry found.")
        return GlobalConfig(**data)

    def get_guild(self, guild: Guild | int, *, create: bool = True) -> GuildConfig:
        if isinstance(guild, Guild):
            guild = guild.id
        data: MutableMapping = self._get_collection("guilds").find_one({"_id": guild})

        if data is None and create:
            document: GuildConfig = GuildConfig(_id=guild)
            self._get_collection("guilds").insert_one(asdict(document))
            data: MutableMapping = self._get_collection("guilds").find_one({"_id": guild})
        elif data is None and not create:
            raise ValueError("No entry found.")
        return GuildConfig(**data)

    def get_channel(self, channel: TextChannel | int, *, create: bool = True) -> ChannelConfig:
        if isinstance(channel, TextChannel):
            channel = channel.id
        data: MutableMapping = self._get_collection("channels").find_one({"_id": channel})

        if data is None and create:
            document: ChannelConfig = ChannelConfig(_id=channel)
            self._get_collection("channels").insert_one(asdict(document))
            data: MutableMapping = self._get_collection("channels").find_one({"_id": channel})
        elif data is None and not create:
            raise ValueError("No entry found.")
        return ChannelConfig(**data)

    def get_user(self, user: User | int, *, create: bool = True) -> UserConfig:
        if isinstance(user, User):
            user = user.id
        data: MutableMapping = self._get_collection("users").find_one({"_id": user})

        if data is None and create:
            document: UserConfig = UserConfig(_id=user)
            self._get_collection("users").insert_one(asdict(document))
            data: MutableMapping = self._get_collection("users").find_one({"_id": user})
        elif data is None and not create:
            raise ValueError("No entry found.")
        return UserConfig(**data)

    def get_member(
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
        data: MutableMapping = self._get_collection("members").find_one(query)

        if data is None and create:
            document: MemberConfig = MemberConfig.create(**query)
            self._get_collection("members").insert_one(asdict(document))
            data: MutableMapping = self._get_collection("members").find_one(query)
        elif data is None and not create:
            raise ValueError("No entry found.")
        return MemberConfig(**data)

    def set_global(self, document: GlobalConfig):
        data: MutableMapping = asdict(document)
        self._get_collection("global").update_one(
            {"_id": document._id}, {"$set": data}, upsert=True
        )

    def set_guild(self, document: GuildConfig):
        data: MutableMapping = asdict(document)
        self._get_collection("guilds").update_one(
            {"_id": document._id}, {"$set": data}, upsert=True
        )

    def set_channel(self, document: ChannelConfig):
        data: MutableMapping = asdict(document)
        self._get_collection("channels").update_one(
            {"_id": document._id}, {"$set": data}, upsert=True
        )

    def set_user(self, document: UserConfig):
        data: MutableMapping = asdict(document)
        self._get_collection("users").update_one(
            {"_id": document._id}, {"$set": data}, upsert=True
        )

    def set_member(self, document: MemberConfig):
        data: MutableMapping = asdict(document)
        self._get_collection("users").update_one(
            {"user_id": document.user_id, "guild_id": document.guild_id},
            {"$set": data},
            upsert=True,
        )
