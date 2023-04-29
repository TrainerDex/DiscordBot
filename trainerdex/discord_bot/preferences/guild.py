from enum import Enum
from zoneinfo import ZoneInfo

import discord as d
from pydantic import BaseModel, Field, validator


class Language(Enum):
    de_DE = "German"
    en_US = "English"
    es_ES = "Spanish"
    fr_FR = "French"
    it_IT = "Italian"
    ja_JP = "Japanese"
    ko_KR = "Korean"
    nl_NL = "Dutch"
    nl_BE = "Dutch, Belgium"
    ro_RO = "Romanian"
    ru_RU = "Russian"
    pt_BR = "Brazilian Portuguese"
    th_TH = "Thai"
    zh_HK = "Traditional Chinese"


class LevelFormat(Enum):
    none = "None"
    int = "40"
    circled_level = "㊵"


class Guild(BaseModel):
    id: int
    language: Language = Field(default=Language.en_US)
    timezone: ZoneInfo | None = Field(default=ZoneInfo("UTC"))
    assign_roles_on_join: bool = True
    set_nickname_on_join: bool = True
    set_nickname_on_update: bool = True
    level_format: LevelFormat = Field(default=LevelFormat.int)
    roles_to_append_on_approval: set[d.Role] = Field(default_factory=set)
    roles_to_remove_on_approval: set[d.Role] = Field(default_factory=set)
    mystic_role: d.Role = None
    valor_role: d.Role = None
    instinct_role: d.Role = None
    tl40_role: d.Role = None
    tl50_role: d.Role = None
    weekly_leaderboards_enabled: bool = False
    leaderboard_channel: d.TextChannel = None
    mod_role_ids: set[d.Role] = Field(default_factory=set)

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
        json_encoders = {
            d.Guild: lambda g: g.id,
            Language: lambda l: l.name,
            ZoneInfo: lambda z: str(z),
            LevelFormat: lambda lf: lf.name,
            d.Role: lambda r: r.id,
            d.TextChannel: lambda tc: tc.id,
        }

    @staticmethod
    def _validate_role(guild: d.Guild, role: d.Role | int) -> d.Role | None:
        if not isinstance(role, (int, d.Role)):
            return None

        if isinstance(role, int):
            return guild.get_role(role)

        if isinstance(role, d.Role) and role.guild == guild:
            return role

    @property
    def guild(self) -> d.Guild:
        from trainerdex.discord_bot.__main__ import bot

        return bot.get_guild(self.id)

    @validator("timezone")
    def validate_timezone(cls, value):
        if isinstance(value, str):
            value = ZoneInfo(value.strip().upper())
        return value

    @validator("roles_to_append_on_approval", "roles_to_remove_on_approval", pre=True)
    def validate_roles(cls, value):
        validated_roles = [cls._validate_role(cls.guild, role) for role in value]
        return {role for role in validated_roles if role is not None}

    @validator("mystic_role", "valor_role", "instinct_role", "tl40_role", "tl50_role", pre=True)
    def validate_role(cls, value):
        return cls._validate_role(cls.guild, value)

    @validator("leaderboard_channel", pre=True)
    def validate_text_channel(cls, value: d.TextChannel | int, values) -> d.TextChannel:
        if isinstance(value, int):
            value = cls.guild.get_channel(value)

        if not isinstance(value, d.TextChannel):
            raise ValueError("Channel must be a TextChannel")
        return value
