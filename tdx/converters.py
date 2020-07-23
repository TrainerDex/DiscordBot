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
    [_("Gray"), _("Green"), _("Teamless"), _("No Team"), _("Team Harmony"), 'Gray', 'Green', 'Teamless', 'No Team', 'Team Harmony'],
    [_("Blue"), _("Mystic"), _("Team Mystic"), "Blue", "Mystic", "Team Mystic"],
    [_("Red"), _("Valor"), _("Team Valor"), "Red", "Valor", "Team Valor"],
    [_("Yellow"), _("Instinct"), _("Team Instinct"), "Yellow", "Instinct", "Team Instinct"],
]


class TeamConverter(commands.Converter):
    async def convert(self, ctx, argument: str) -> Team:
        if argument.lower() in team_search_values[0]:
            return Team(0, _("Teamless"), '#929292')
        elif argument.lower() in team_search_values[1]:
            return Team(0, _("Team Mystic"), '#0005ff')
        elif argument.lower() in team_search_values[2]:
            return Team(0, _("Team Valor"), '#ff0000')
        elif argument.lower() in team_search_values[3]:
            return Team(0, _("Team Instinct"), '#fff600')
