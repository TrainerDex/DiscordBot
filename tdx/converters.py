import datetime
import re
from typing import Union

import discord
from discord.ext import commands

from dateutil.parser import parse, ParserError
from redbot.core.i18n import Translator
import trainerdex
from tdx.models import Faction

_ = Translator("TrainerDex", __file__)




class TrainerConverter(commands.Converter):
    """Converts to a :class:`~trainerdex.Trainer`.
    
    The lookup strategy is as follows (in order):
    1. Lookup by nickname.
    2. Lookup by Discord User
    """

    async def convert(self, ctx, argument) -> trainerdex.Trainer:
        if isinstance(argument, (discord.User, discord.Member)):
            match = None
            mention = argument
        else:
            match = re.match(r"[A-Za-z0-9]{3,15}$", argument)
            mention = None

        if match is None:
            # not a Valid Pogo name
            # check if mention
            if mention is None:
                try:
                    mention = await commands.converter.UserConverter().convert(ctx, argument)
                except commands.BadArgument:
                    result = None
                    mention = None

            if mention:
                try:
                    result = (
                        trainerdex.Client()
                        .get_discord_user(uid=[str(mention.id)])[0]
                        .owner()
                        .trainer()[0]
                    )
                except IndexError:
                    result = None
        else:
            result = trainerdex.Client().get_trainer_from_username(argument)

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
        if argument.isnumeric():
            if int(argument) < len(self.teams):
                result = Faction(**self.teams[int(argument)])
            else:
                result = None
        else:
            options = [
                x for x in self.teams if argument.casefold() in map(str.casefold, x.get("lookups"))
            ]
            if len(options) == 1:
                result = Faction(**options[0])
            else:
                result = None

        if result is None:
            raise commands.BadArgument(_("Faction `{}` not found").format(argument))

        return result
