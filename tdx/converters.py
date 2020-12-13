import contextlib
import logging
import re
from typing import Any, Union

import discord
from redbot.core import commands
from redbot.core.i18n import Translator
from trainerdex.client import Client
from trainerdex.faction import Faction
from trainerdex.trainer import Trainer
from trainerdex.update import Level, get_level

logger: logging.Logger = logging.getLogger(__name__)
_ = Translator("TrainerDex", __file__)


class SafeConvertObject:
    def __init__(self, e: str):
        self.e: str = str(e)

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return f"SafeConvertObject: {self.e}"

    def __str__(self) -> str:
        return self.e

    def __eq__(self, other: Any) -> bool:
        if other is None:
            return True
        if isinstance(other, SafeConvertObject):
            return self.e == other.e

    def __hash__(self):
        return hash(self.e)


async def safe_convert(
    converter: commands.Converter, *args, **kwargs
) -> Union[Any, SafeConvertObject]:
    """Convenience method for returning None or a default if the conversion failed"""
    try:
        return await converter().convert(*args, **kwargs)
    except commands.BadArgument as e:
        return kwargs.get("default", SafeConvertObject(e))


class NicknameConverter(commands.Converter):
    @property
    def regex(self) -> str:
        return r"[A-Za-z0-9]{3,15}$"

    async def convert(self, ctx: commands.Context, argument: str) -> str:
        logger.debug("NicknameConverter: argument: %s", argument)

        match: Union[re.Match, None] = re.match(self.regex, argument)
        if match is None:
            raise commands.BadArgument(
                _(
                    "{} is not a valid Pokémon Go username. "
                    "A Pokémon Go username is 3-15 letters or numbers long."
                ).format(argument)
            )
        return argument


class TrainerConverter(commands.Converter):
    """Converts to a :class:`trainerdex.Trainer`.

    The lookup strategy is as follows (in order):
    1. Lookup by nickname.
    2. Lookup by Discord User
    """

    async def convert(
        self,
        ctx: commands.Context,
        argument: Union[str, discord.User, discord.Member],
        cli: Client = Client(),
    ) -> Trainer:
        logger.debug("TrainerConverter: argument: %s", argument)

        mention = None
        if isinstance(argument, str):
            is_valid_nickname = await safe_convert(NicknameConverter, ctx, argument)
            if is_valid_nickname:
                with contextlib.suppress(IndexError):
                    trainer = await cli.search_trainer(argument)
                    await trainer.fetch_updates()
                    return trainer

            is_mention = await safe_convert(
                discord.ext.commands.converter.UserConverter, ctx, argument
            )
            if is_mention:
                mention = is_mention
        elif isinstance(argument, (discord.User, discord.Member)):
            mention = argument

        if mention:
            socialconnections = await cli.get_social_connections("discord", str(mention.id))
            if socialconnections:
                trainer = await socialconnections[0].trainer()
                await trainer.fetch_updates()
                return trainer

        raise commands.BadArgument(_("Trainer `{}` not found").format(argument))


class TeamConverter(commands.Converter):
    def __init__(self):
        self.teams = {
            0: ["Gray", "Green", "Teamless", "No Team", "Team Harmony"],
            1: ["Blue", "Mystic", "Team Mystic"],
            2: ["Red", "Valor", "Team Valor"],
            3: ["Yellow", "Instinct", "Team Instinct"],
        }

    async def convert(self, ctx: commands.Context, argument: str) -> Faction:
        logger.debug("TeamConverter: argument: %s", argument)
        if isinstance(argument, int) or argument.isnumeric():
            if int(argument) in self.teams.keys():
                result = Faction(int(argument))
                result._update(self.teams[int(argument)])  # Ensures team names are translated
            else:
                result = None
        else:
            options = [
                k for k, v in self.teams.items() if argument.casefold() in map(str.casefold, v)
            ]
            if len(options) == 1:
                result: Faction = Faction(options[0])
            else:
                result = None

        if result is None:
            raise commands.BadArgument(_("Team `{}` not found").format(argument))

        return result


class LevelConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> Level:
        logger.debug("LevelConverter: argument: %s", argument)
        try:
            return get_level(level=int(argument))
        except KeyError:
            raise commands.BadArgument(_("Not a valid level. Please choose between 1-40"))


class TotalXPConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> Level:
        logger.debug("TotalXPConverter: argument: %s", argument)
        if not argument.isdigit():
            raise commands.BadArgument(_("Not a valid number."))
        elif int(argument) < 100:
            raise commands.BadArgument(_("Value too low."))
        else:
            return int(argument)


class TrainerCodeValidator(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> str:
        logger.debug("TrainerCodeValidator: argument: %s", argument)
        if re.match(r"^(\d{4}[\s-]?){3}$", argument):
            return re.sub(r"[\s-]", "", argument)
        else:
            raise commands.BadArgument(
                _("Trainer Code must be 12 digits long and contain only numbers and whitespace.")
            )
