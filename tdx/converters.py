from datetime import date
from dateutil.parser import parse, ParserError

from discord.ext import commands

from trainerdex import get_team
from trainerdex.utils import TeamTuple


class TeamConverter(commands.Converter):
    async def convert(self, ctx, argument: str) -> TeamTuple:
        if argument.lower() in ['grey', 'green', 'teamless', 'no team']:
            return get_team(0)
        elif argument.lower() in ['mystic', 'blue']:
            return get_team(1)
        elif argument.lower() in ['valor', 'red', 'valour']:
            return get_team(2)
        elif argument.lower() in ['instinct', 'yellow']:
            return get_team(3)


class DateConverter(commands.Converter):
    async def convert(self, ctx, argument: str) -> datetime.date:
        try:
            return parse(argument).date()
        except ParserError:
            return None
