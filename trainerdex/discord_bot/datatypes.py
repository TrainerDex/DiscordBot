from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Mapping
from uuid import UUID, uuid4

from discord import Bot
from discord.role import Role

if TYPE_CHECKING:
    from typing_extensions import Self

    from trainerdex.discord_bot.config import Config


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

    @classmethod
    def from_mapping(cls, mapping: Mapping) -> Self:
        return cls(**{k: v for k, v in mapping.items() if k in inspect.signature(cls).parameters})


@dataclass
class GlobalConfig(_MongoDBDocument):
    embed_footer: str = "Provided with ❤️ by TrainerDex"
    notice: str | None = None


@dataclass
class CogMeta(_MongoDBDocument):
    _id: str
    enabled: bool = True
    last_loaded: datetime | None = None

    @property
    def cog_name(self) -> str:
        return self._id


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

    timezone: str = None
    post_weekly_leaderboards: bool = False
    leaderboard_channel_id: int | None = None

    mod_role_ids: list[int] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, mapping: Mapping) -> Self:
        mapping = dict(mapping)
        mapping["roles_to_assign_on_approval"] = StoredRoles(
            **mapping.pop("roles_to_assign_on_approval", {})
        )
        return cls(**{k: v for k, v in mapping.items() if k in inspect.signature(cls).parameters})

    @property
    def is_eligible_for_leaderboard(self) -> bool:
        return self.post_weekly_leaderboards and self.leaderboard_channel_id is not None


@dataclass
class ChannelConfig(_MongoDBDocument):
    pass


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
