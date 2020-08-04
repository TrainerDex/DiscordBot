import re
from typing import Any, Dict, List, Union

import discord
from discord.ext import commands

from redbot.core.i18n import Translator
from tdx.client.client import Client
from tdx.client.trainer import Trainer
from tdx.models import Faction

_ = Translator("TrainerDex", __file__)


class SafeConvertException:
    def __init__(self, **kwargs):
        self.e = kwargs.get("e")

    def __bool__(self):
        return False

    def __repr__(self):
        return "SafeConvertEmpty"

    def __eq__(self, other):
        if other is None:
            return True
        if isinstance(other, SafeConvertException):
            return self.e == other.e


async def safe_convert(converter, ctx, argument) -> Union[Any, SafeConvertException]:
    """Convenience method for returning `SafeConvertException` if the conversion failed"""
    try:
        return await converter().convert(ctx, argument)
    except commands.BadArgument as e:
        return SafeConvertException(e=e)


class NicknameConverter(commands.Converter):
    @property
    def regex(self):
        return r"[A-Za-z0-9]{3,15}$"

    async def convert(self, ctx, argument: str) -> str:
        match: Union[re.Match, None] = re.match(self.regex, argument)
        if match is None:
            raise commands.BadArgument(
                _(
                    "{} is not a valid Pokemon Go username. A Pokemon Go username is 3-15 letters or numbers long."
                ).format(argument)
            )
        return argument


class TrainerConverter(commands.Converter):
    """Converts to a :class:`tdx.client.Trainer`.

    The lookup strategy is as follows (in order):
    1. Lookup by nickname.
    2. Lookup by Discord User
    """

    async def convert(self, ctx, argument) -> Trainer:
        if isinstance(argument, (discord.User, discord.Member)):
            match = None
            mention: Union[discord.User, discord.Member] = argument
        else:
            try:
                match: str = await NicknameConverter().convert(ctx, argument)
            except commands.BadArgument:
                match = None
            mention = None

        if match is None:
            # not a Valid Pogo name
            # check if mention
            if mention is None:
                try:
                    mention: discord.User = await commands.converter.UserConverter().convert(
                        ctx, argument
                    )
                except commands.BadArgument:
                    result = None
                    mention = None

            if mention:
                socialconnections = Client().get_social_connections("discord", str(mention.id))
                if socialconnections:
                    result = await socialconnections[0].trainer()
                else:
                    result = None
        else:
            result: Trainer = Client().search_trainer(argument)

        if result is None:
            raise commands.BadArgument(_("Trainer `{}` not found").format(argument))

        return result


class TeamConverter(commands.Converter):
    def __init__(self):
        self.teams = [
            {
                "id": 0,
                "verbose_name": _("Teamless"),
                "colour": 9605778,
                "lookups": ["Gray", "Green", "Teamless", "No Team", "Team Harmony"],
            },
            {
                "id": 1,
                "verbose_name": _("Mystic"),
                "colour": 1535,
                "lookups": ["Blue", "Mystic", "Team Mystic"],
            },
            {
                "id": 2,
                "verbose_name": _("Valor"),
                "colour": 16711680,
                "lookups": ["Red", "Valor", "Team Valor"],
            },
            {
                "id": 3,
                "verbose_name": _("Instinct"),
                "colour": 16774656,
                "lookups": ["Yellow", "Instinct", "Team Instinct"],
            },
        ]

    async def convert(self, ctx, argument: str) -> Faction:
        if isinstance(argument, int) or argument.isnumeric():
            if int(argument) < len(self.teams):
                result = Faction(int(argument))
                result._update(self.teams[int(argument)])  # Ensures team names are translated
            else:
                result = None
        else:
            options: List[Dict[str, Union[int, str]]] = [
                x for x in self.teams if argument.casefold() in map(str.casefold, x.get("lookups"))
            ]
            if len(options) == 1:
                result: Faction = Faction(**options[0])
            else:
                result = None

        if result is None:
            raise commands.BadArgument(_("Faction `{}` not found").format(argument))

        return result
