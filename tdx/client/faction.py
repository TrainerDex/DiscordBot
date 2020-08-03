FACTION_DATA = [
    {"id": 0, "verbose_name": "Teamless", "colour": 9605778,},
    {"id": 1, "verbose_name": "Mystic", "colour": 1535,},
    {"id": 2, "verbose_name": "Valor", "colour": 16711680,},
    {"id": 3, "verbose_name": "Instinct", "colour": 16774656,},
]


class Faction:
    def __new__(self, id: str):
        instance.__init__(**FACTION_DATA[id])
        return instance

    def __init__(self, **data):
        self._update(data)

    def _update(self, data):
        self.id = int(data.get("id"))
        self.verbose_name = data.get("verbose_name")
        self.colour = data.get("colour")
        self.color = self.colour

    def __str__(self) -> str:
        return self.verbose_name
