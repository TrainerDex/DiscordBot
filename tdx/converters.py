import datetime
import re
from typing import Union

import discord
from discord.ext import commands

from dateutil.parser import parse, ParserError
from redbot.core.i18n import Translator
import trainerdex
from tdx.models import Team

_ = Translator("TrainerDex", __file__)

team_search_values = [
    ["Gray", "Green", "Teamless", "No Team", "Team Harmony"],
    ["Blue", "Mystic", "Team Mystic"],
    ["Red", "Valor", "Team Valor"],
    ["Yellow", "Instinct", "Team Instinct"],
]


class TrainerConverter(commands.Converter):
    """Converts to a :class:`~trainerdex.Trainer`.
    
    The lookup strategy is as follows (in order):
    1. Lookup by nickname.
    2. Lookup by Discord User
    """

    async def convert(self, ctx, argument) -> trainerdex.Trainer:
        print("TrainerConverter: ", argument, type(argument))

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
            raise commands.BadArgument('Trainer "{}" not found'.format(argument))

        return result


class TeamConverter(commands.Converter):
    async def convert(self, ctx, argument: str) -> Team:
        if argument.lower() in [x.lower() for x in team_search_values[0]]:
            return Team(0, _("Teamless"), "#929292")
        elif argument.lower() in [x.lower() for x in team_search_values[1]]:
            return Team(1, _("Mystic"), "#0005ff")
        elif argument.lower() in [x.lower() for x in team_search_values[2]]:
            return Team(2, _("Valor"), "#ff0000")
        elif argument.lower() in [x.lower() for x in team_search_values[3]]:
            return Team(3, _("Instinct"), "#fff600")
