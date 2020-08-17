import logging
import os
from abc import ABC
from typing import Final

import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting as cf

import PogoOCR
from . import converters, client
from .create import ProfileCreate
from .embeds import ProfileCard
from .leaderboard import Leaderboard
from .profile import Profile
from .settings import Settings
from .utils import append_twitter, check_xp, loading

log: logging.Logger = logging.getLogger(__name__)
POGOOCR_TOKEN_PATH: Final = os.path.join(os.path.dirname(__file__), "data/key.json")
_ = Translator("TrainerDex", __file__)


class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """

    pass


class TrainerDex(
    ProfileCreate, Profile, Leaderboard, Settings, commands.Cog, metaclass=CompositeMetaClass
):
    def __init__(self, bot: Red) -> None:
        self.bot: Red = bot
        self.config: Config = Config.get_conf(
            None, cog_name="trainerdex", identifier=8124637339, force_registration=True,
        )
        self.config.register_global(
            **{"embed_footer": "Provided with ❤️ by TrainerDex", "notice": None}
        )
        self.config.register_guild(
            **{
                "assign_roles_on_join": True,
                "set_nickname_on_join": True,
                "set_nickname_on_update": True,
                "roles_to_assign_on_approval": {"add": [], "remove": []},
                "mystic_role": None,
                "valor_role": None,
                "instinct_role": None,
                "tl40_role": None,
                "introduction_note": None,
            }
        )
        self.config.register_channel(**{"profile_ocr": False})
        self.client = None
        self.emoji = {
            "teamless": self.bot.get_emoji(743873748029145209),
            "mystic": self.bot.get_emoji(430113444558274560),
            "valor": self.bot.get_emoji(430113457149575168),
            "instinct": self.bot.get_emoji(430113431333371924),
            "travel_km": self.bot.get_emoji(743122298126467144),
            "capture_total": self.bot.get_emoji(743122649529450566),
            "pokestops_visited": self.bot.get_emoji(743122864303243355),
            "total_xp": self.bot.get_emoji(743121748630831165),
            "gift": self.bot.get_emoji(743120044615270616),
            "add_friend": self.bot.get_emoji(743853499170947234),
            "previous": self.bot.get_emoji(729769958652772505),
            "next": self.bot.get_emoji(729770058099982347),
            "loading": self.bot.get_emoji(471298325904359434),
            "global": self.bot.get_emoji(743853198217052281),
            "gym": self.bot.get_emoji(743874196639056096),
            "gym_badge": self.bot.get_emoji(743853262469333042),
            "number": "#",
            "profile": self.bot.get_emoji(743853381919178824),
            "date": self.bot.get_emoji(743874800547791023),
        }

        assert os.path.isfile(POGOOCR_TOKEN_PATH)  # Looks for a Google Cloud Token

    async def initialize(self) -> None:
        await self._create_client()

    async def _create_client(self) -> None:
        """Create TrainerDex API Client"""
        token = await self._get_token()
        self.client = client.Client(token=token)

    async def _get_token(self) -> str:
        """Get TrainerDex token"""
        api_tokens = await self.bot.get_shared_api_tokens("trainerdex")
        token = api_tokens.get("token", "")
        if not token:
            log.warning("No valid token found")
        return token

    @commands.Cog.listener("on_message")
    async def check_screenshot(self, source_message: discord.Message) -> None:
        if source_message.author.bot:
            return

        profile_ocr: bool = await self.config.channel_from_id(
            source_message.channel.id
        ).profile_ocr()
        if not profile_ocr:
            return

        if len(source_message.attachments) != 1:
            return

        await source_message.add_reaction(self.bot.get_emoji(471298325904359434))

        try:
            trainer: client.Trainer = await converters.TrainerConverter().convert(
                None, source_message.author, cli=self.client
            )
        except discord.ext.commands.errors.BadArgument:
            await source_message.remove_reaction(
                self.bot.get_emoji(471298325904359434), self.bot.user
            )
            await source_message.add_reaction("\N{THUMBS DOWN SIGN}")
            await source_message.channel.send(
                "{message.author.mention} Trainer not found!", delete_after=5
            )
            return

        async with source_message.channel.typing():
            try:
                message: discord.Message = await source_message.channel.send(
                    loading(_("That's a nice image you have there, let's see…"))
                )
                ocr = PogoOCR.ProfileSelf(
                    POGOOCR_TOKEN_PATH, image_uri=source_message.attachments[0].proxy_url
                )
                ocr.get_text()

                data_found = {
                    "travel_km": ocr.travel_km,
                    "capture_total": ocr.capture_total,
                    "pokestops_visited": ocr.pokestops_visited,
                    "total_xp": ocr.total_xp,
                }

                if data_found.get("total_xp"):
                    await message.edit(
                        content=append_twitter(
                            loading(
                                _(
                                    "{user}, we found the following stats:\n"
                                    "{stats}\nJust processing that now…"
                                )
                            ).format(user=source_message.author.mention, stats=cf.box(data_found))
                        )
                    )

                    if max(trainer.updates, key=check_xp).total_xp > data_found.get("total_xp"):
                        await message.edit(
                            content=append_twitter(
                                cf.warning(
                                    _(
                                        "You've previously set your XP to higher than what you're trying to set it to. "
                                        "It's currently set to {xp}."
                                    )
                                )
                            ).format(xp=cf.humanize_number(data_found.get("total_xp")))
                        )
                        await source_message.remove_reaction(
                            self.bot.get_emoji(471298325904359434), self.bot.user
                        )
                        await source_message.add_reaction(
                            "\N{WARNING SIGN}\N{VARIATION SELECTOR-16}"
                        )
                        return
                    elif max(trainer.updates, key=check_xp).total_xp == data_found.get("total_xp"):
                        text: str = cf.warning(
                            _(
                                "You've already set your XP to this figure. "
                                "In future, to see the output again, please run the `progress` command as it costs us to run OCR."
                            )
                        )
                        await source_message.remove_reaction(
                            self.bot.get_emoji(471298325904359434), self.bot.user
                        )
                        await source_message.add_reaction(
                            "\N{WARNING SIGN}\N{VARIATION SELECTOR-16}"
                        )
                    else:
                        await trainer.post(
                            stats=data_found,
                            data_source="ss_ocr",
                            update_time=source_message.created_at,
                        )
                        await source_message.remove_reaction(
                            self.bot.get_emoji(471298325904359434), self.bot.user
                        )
                        await source_message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
                        text = None

                    if source_message.guild and not trainer.is_visible:
                        await message.edit(_("Sending in DMs"))
                        message = await source_message.author.send(
                            content=loading(_("Loading output…"))
                        )

                    await message.edit(
                        content="\n".join(
                            [x for x in [text, loading(_("Loading output…"))] if x is not None]
                        )
                    )
                    embed: discord.Embed = await ProfileCard(
                        ctx=source_message,
                        bot=self.bot,
                        client=self.client,
                        trainer=trainer,
                        emoji=self.emoji,
                    )
                    await message.edit(
                        content="\n".join(
                            [x for x in [text, loading(_("Loading output…"))] if x is not None]
                        )
                    )
                    await embed.show_progress()
                    await message.edit(
                        content="\n".join(
                            [
                                x
                                for x in [text, loading(_("Loading leaderboards…"))]
                                if x is not None
                            ]
                        ),
                        embed=embed,
                    )
                    await embed.add_leaderboard()
                    if source_message.guild:
                        await message.edit(embed=embed)
                        await embed.add_guild_leaderboard(source_message.guild)
                    await message.edit(content=text, embed=embed)
                else:
                    await message.edit(
                        content=cf.error(_("I could not find Total XP in your image. "))
                        + "\n\n"
                        + cf.info(
                            _(
                                "We use Google Vision API to read your images. "
                                "Please ensure that the ‘Total XP’ field is visible. "
                                "If it is visible and your image still doesn't scan after a minute, try a new image. "
                                "Posting the same image again, will likely cause another failure."
                            )
                        )
                    )
                    await source_message.remove_reaction(
                        self.bot.get_emoji(471298325904359434), self.bot.user
                    )
                    await source_message.add_reaction("\N{THUMBS DOWN SIGN}")
            except Exception as e:
                await source_message.channel.send(
                    "`Error in function 'check_screenshot'."
                    " Check your console or logs for details.`"
                )
                raise e
