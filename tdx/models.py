from typing import List

import discord

import trainerdex
from tdx.client.faction import Faction as BaseFaction


class Faction(BaseFaction):
    def _update(self, **data):
        super()._update(data)
        self.lookups: List[str] = lookups


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
