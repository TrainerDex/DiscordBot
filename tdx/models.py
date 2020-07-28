from typing import List

import discord

import trainerdex


class Faction:
    def __init__(self, id: int, verbose_name: str, colour: discord.Colour, lookups: List[str]):
        self.id: int = id
        self.verbose_name: str = verbose_name
        self.colour: discord.Colour = colour
        self.color: discord.Colour = self.colour
        self.lookups: List[str] = lookups

    def __str__(self):
        return self.verbose_name


Team = Faction


class UserData:
    def __init__(self, **kwargs):
        self.trainer: trainerdex.Trainer = kwargs.get("trainer", None)
        self.team: Faction = kwargs.get("team", None)
        self.updates: List[trainerdex.Update] = kwargs.get("updates", None)
        self.update: trainerdex.Update = kwargs.get("update", None)

    @property
    def level(self):
        if self.update:
            return self.update.level()
        else:
            return self.trainer.level()
