import datetime

from discord.ext import commands

from dateutil.parser import parse, ParserError
from redbot.core.i18n import Translator

_ = Translator("TrainerDex", __file__)


class Team:
    def __init__(self, id: int, name: str, colour: str):
        self.id = id
        self.name = name
        self.colour = colour

team_search_values = [
    ['Gray', 'Green', 'Teamless', 'No Team', 'Team Harmony'],
    ["Blue", "Mystic", "Team Mystic"],
    ["Red", "Valor", "Team Valor"],
    ["Yellow", "Instinct", "Team Instinct"],
]


class TeamConverter(commands.Converter):
    async def convert(self, ctx, argument: str) -> Team:
        if argument.lower() in [x.lower() for x in team_search_values[0]]:
            return Team(0, _("Teamless"), '#929292')
        elif argument.lower() in [x.lower() for x in team_search_values[1]]:
            return Team(1, _("Team Mystic"), '#0005ff')
        elif argument.lower() in [x.lower() for x in team_search_values[2]]:
            return Team(2, _("Team Valor"), '#ff0000')
        elif argument.lower() in [x.lower() for x in team_search_values[3]]:
            return Team(3, _("Team Instinct"), '#fff600')
