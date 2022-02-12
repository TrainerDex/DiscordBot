import contextlib
import logging
import re
from typing import Any, Dict, List, Literal, Union

from discord.abc import User
from discord.ext.commands import BadArgument, Converter, Context, UserConverter

from trainerdex.client import Client
from trainerdex.faction import Faction
from trainerdex.socialconnection import SocialConnection
from trainerdex.trainer import Trainer
from trainerdex.update import Level, get_level

logger: logging.Logger = logging.getLogger(__name__)


class SafeConvertObject:
    def __init__(self, exception: str) -> None:
        self.exception: str = str(exception)

    def __bool__(self) -> Literal[False]:
        return False

    def __repr__(self) -> str:
        return f"<{__name__}: {self.exception}>"

    def __str__(self) -> str:
        return self.exception

    def __eq__(self, other: Any) -> bool:
        if other is None:
            return True
        if isinstance(other, SafeConvertObject):
            return self.exception == other.exception

    def __hash__(self):
        return hash(self.exception)


async def safe_convert(converter: Converter, *args, **kwargs) -> Union[Any, SafeConvertObject]:
    """Convenience method for returning None or a default if the conversion failed"""
    try:
        return await converter().convert(*args, **kwargs)
    except BadArgument as e:
        return kwargs.get("default", SafeConvertObject(e))


class NicknameConverter(Converter):
    @property
    def regex(self) -> str:
        return r"[A-Za-z0-9]{3,15}$"

    async def convert(self, ctx: Context, argument: str) -> str:
        logger.debug("NicknameConverter: argument: %s", argument)

        match: Union[re.Match, None] = re.match(self.regex, argument)
        if match is None:
            raise BadArgument(
                f"{argument} is not a valid Pokémon Go username. A Pokémon Go username is 3-15 letters or numbers long."
            )
        return argument


class TrainerConverter(Converter):
    """Converts to a :class:`trainerdex.Trainer`.

    The lookup strategy is as follows (in order):
    1. Lookup by nickname.
    2. Lookup by Discord User
    """

    async def convert(
        self,
        ctx: Context,
        argument: Union[str, User],
        cli: Client = Client(),
    ) -> Trainer:
        logger.debug("TrainerConverter: argument: %s", argument)

        mention: Union[User, None] = None
        if isinstance(argument, str):
            is_valid_nickname: Union[str, SafeConvertObject] = await safe_convert(
                NicknameConverter,
                ctx,
                argument,
            )
            if is_valid_nickname:
                with contextlib.suppress(IndexError):
                    trainer: Trainer = await cli.search_trainer(argument)
                    await trainer.fetch_updates()
                    return trainer

            is_mention: Union[User, SafeConvertObject] = await safe_convert(
                UserConverter,
                ctx,
                argument,
            )
            if is_mention:
                mention = is_mention
        elif isinstance(argument, User):
            mention = argument

        if mention:
            socialconnections: List[SocialConnection] = await cli.get_social_connections(
                "discord",
                str(mention.id),
            )
            if socialconnections:
                trainer: Trainer = await socialconnections[0].trainer()
                await trainer.fetch_updates()
                return trainer

        raise BadArgument(f"Trainer `{argument}` not found")


class TeamConverter(Converter):
    def __init__(self):
        self.teams: Dict[int, List[str]] = {
            0: ["Gray", "Green", "Teamless", "No Team", "Team Harmony"],
            1: ["Blue", "Mystic", "Team Mystic"],
            2: ["Red", "Valor", "Team Valor"],
            3: ["Yellow", "Instinct", "Team Instinct"],
        }

    async def convert(self, ctx: Context, argument: str) -> Faction:
        logger.debug("TeamConverter: argument: %s", argument)

        result: Union[Faction, None] = None

        if isinstance(argument, int) or argument.isnumeric():
            if int(argument) in self.teams.keys():
                result = Faction(int(argument))
                result._update(self.teams[int(argument)])  # Ensures team names are translated
        else:
            options = [
                k for k, v in self.teams.items() if argument.casefold() in map(str.casefold, v)
            ]
            if len(options) == 1:
                result = Faction(options[0])

        if result is None:
            raise BadArgument(f"Team `{argument}` not found")

        return result


class LevelConverter(Converter):
    async def convert(self, ctx: Context, argument: str) -> Level:
        logger.debug("LevelConverter: argument: %s", argument)
        try:
            return get_level(level=int(argument))
        except KeyError:
            raise BadArgument("Not a valid level. Please choose between 1-40")


class TotalXPConverter(Converter):
    async def convert(self, ctx: Context, argument: str) -> int:
        logger.debug("TotalXPConverter: argument: %s", argument)
        if not argument.isdigit():
            raise BadArgument("Not a valid number.")
        elif int(argument) < 100:
            raise BadArgument("Value too low.")
        else:
            return int(argument)


class TrainerCodeValidator(Converter):
    async def convert(self, ctx: Context, argument: str) -> str:
        logger.debug("TrainerCodeValidator: argument: %s", argument)
        if re.match(r"^(\d{4}[\s-]?){3}$", argument):
            return re.sub(r"[\s-]", "", argument)
        else:
            raise BadArgument(
                "Trainer Code must be 12 digits long and contain only numbers and whitespace."
            )
