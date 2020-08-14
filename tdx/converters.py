import datetime
import re
from typing import Any, Union

import discord
from dateutil.parser import parse
from discord.ext import commands

from redbot.core.i18n import Translator
from . import client

_ = Translator("TrainerDex", __file__)


class SafeConvertObject:
    def __init__(self, e):
        self.e = e

    def __bool__(self):
        return False

    def __repr__(self):
        return "SafeConvertEmpty"

    def __eq__(self, other):
        if other is None:
            return True
        if isinstance(other, SafeConvertObject):
            return self.e == other.e


async def safe_convert(converter, ctx, argument) -> Union[Any, SafeConvertObject]:
    """Convenience method for returning `SafeConvertException` if the conversion failed"""
    try:
        return await converter().convert(ctx, argument)
    except commands.BadArgument as e:
        return SafeConvertObject(e=e)


class NicknameConverter(commands.Converter):
    @property
    def regex(self):
        return r"[A-Za-z0-9]{3,15}$"

    async def convert(self, ctx, argument: str) -> str:
        match: Union[re.Match, None] = re.match(self.regex, argument)
        if match is None:
            raise commands.BadArgument(
                _(
                    "{} is not a valid Pokemon Go username. "
                    "A Pokemon Go username is 3-15 letters or numbers long."
                ).format(argument)
            )
        return argument


class TrainerConverter(commands.Converter):
    """Converts to a :class:`tdx.client.Trainer`.

    The lookup strategy is as follows (in order):
    1. Lookup by nickname.
    2. Lookup by Discord User
    """

    async def convert(self, ctx, argument, cli=client.Client()) -> client.Trainer:

        mention = None
        if isinstance(argument, str):
            is_valid_nickname = await safe_convert(NicknameConverter, ctx, argument)
            is_mention = await safe_convert(commands.converter.UserConverter, ctx, argument)
            if is_valid_nickname:
                try:
                    return await cli.search_trainer(argument)
                except IndexError:
                    pass
                mention = None

            if is_mention:
                mention = is_mention
        elif isinstance(argument, (discord.User, discord.Member)):
            mention = argument

        if mention:
            socialconnections = await cli.get_social_connections("discord", str(mention.id))
            if socialconnections:
                return await socialconnections[0].trainer()

        raise commands.BadArgument(_("Trainer `{}` not found").format(argument))


class TeamConverter(commands.Converter):
    def __init__(self):
        self.teams = {
            0: ["Gray", "Green", "Teamless", "No Team", "Team Harmony"],
            1: ["Blue", "Mystic", "Team Mystic"],
            2: ["Red", "Valor", "Team Valor"],
            3: ["Yellow", "Instinct", "Team Instinct"],
        }

    async def convert(self, ctx, argument: str) -> client.Faction:
        if isinstance(argument, int) or argument.isnumeric():
            if int(argument) in self.teams.keys():
                result = client.Faction(int(argument))
                result._update(self.teams[int(argument)])  # Ensures team names are translated
            else:
                result = None
        else:
            options = [
                k for k, v in self.teams.items() if argument.casefold() in map(str.casefold, v)
            ]
            if len(options) == 1:
                result: client.Faction = client.Faction(options[0])
            else:
                result = None

        if result is None:
            raise commands.BadArgument(_("Faction `{}` not found").format(argument))

        return result


class LevelConverter(commands.Converter):
    async def convert(self, ctx, argument: str) -> client.Level:
        try:
            return client.update.get_level(level=int(argument))
        except:
            raise commands.BadArgument()


class DatetimeConverter(commands.Converter):
    async def convert(self, ctx, argument: str) -> datetime.datetime:
        return parse(argument)


class DateConverter(DatetimeConverter):
    async def convert(self, ctx, argument: str) -> datetime.date:
        return await super().convert(ctx, argument).date()
