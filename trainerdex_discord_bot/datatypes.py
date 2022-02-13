from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from discord import Bot
from discord.role import Role

from trainerdex_discord_bot.constants import DEFAULT_PREFIX

if TYPE_CHECKING:
    from trainerdex.client import Client
    from trainerdex_discord_bot.config import Config


@dataclass
class StoredRoles:
    add: list[int] = field(default_factory=list)
    remove: list[int] = field(default_factory=list)


@dataclass
class TransformedRoles:
    add: list[Role] = field(default_factory=list)
    remove: list[Role] = field(default_factory=list)


@dataclass
class _MongoDBDocument:
    _id: int


@dataclass
class GlobalConfig(_MongoDBDocument):
    embed_footer: str = "Provided with ❤️ by TrainerDex"
    notice: str | None = None


@dataclass
class GuildConfig(_MongoDBDocument):
    assign_roles_on_join: bool = True
    set_nickname_on_join: bool = True
    set_nickname_on_update: bool = True
    roles_to_assign_on_approval: StoredRoles = field(default_factory=StoredRoles)
    mystic_role: int | None = None
    valor_role: int | None = None
    instinct_role: int | None = None
    tl40_role: int | None = None
    introduction_note: str | None = None
    enabled: bool = True
    prefix: str = DEFAULT_PREFIX


@dataclass
class ChannelConfig(_MongoDBDocument):
    profile_ocr: bool = False


@dataclass
class UserConfig(_MongoDBDocument):
    pass


@dataclass
class MemberConfig(UserConfig):
    _uid: UUID
    user_id: int
    guild_id: int

    @classmethod
    def create(cls, *args, **kwargs) -> MemberConfig:
        return cls(uuid=uuid4(), *args, **kwargs)


@dataclass
class Common:
    bot: Bot
    config: Config
    client: Client
