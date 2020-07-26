from typing import List

from discord.colour import Colour


class Faction:
    def __init__(self, id: int, verbose_name: str, colour: Colour, lookups: List[str]):
        self.id: int = id
        self.verbose_name: str = verbose_name
        self.colour: discord.Colour = colour
        self.color: discord.Colour = self.colour
        self.lookups: List[str] = lookups

    def __str__(self):
        return self.verbose_name


Team = Faction
