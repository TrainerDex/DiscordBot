from dataclasses import dataclass
from discord.role import Role
from typing import List, Optional, TypedDict


class StoredRoles(TypedDict):
    add: List[int]
    remove: List[int]


class TransformedRoles(TypedDict):
    add: List[Role]
    remove: List[Role]


@dataclass
class GlobalConfig:
    embed_footer: str
    notice: Optional[str] = None


@dataclass
class GuildConfig:
    assign_roles_on_join: bool
    set_nickname_on_join: bool
    set_nickname_on_update: bool
    roles_to_assign_on_approval: StoredRoles
    mystic_role: Optional[int] = None
    valor_role: Optional[int] = None
    instinct_role: Optional[int] = None
    tl40_role: Optional[int] = None
    introduction_note: Optional[str] = None


@dataclass
class ChannelConfig:
    profile_ocr: bool
