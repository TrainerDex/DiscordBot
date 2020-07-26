from typing import List

from discord.colour import Colour


class Faction:
    def __init__(self, id: int, verbose_name: str, colour: Colour, lookups: List[str]):
        self.id = id
        self.verbose_name = verbose_name
        self.colour = colour
        self.color = self.colour
        self.lookups = lookups

    def __str__(self):
        return self.verbose_name


Team = Faction
