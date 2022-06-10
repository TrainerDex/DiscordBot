import textwrap
from decimal import ROUND_HALF_UP, Decimal
from io import BytesIO
from typing import Iterator, Sequence

import discord
import humanize

from trainerdex_discord_bot.constants import CustomEmoji


def loading(text: str) -> str:
    """Get the given text with a loading indicator.

    Parameters
    ----------
    text : str
        The text to be marked up.

    Returns
    -------
    str
        The marked up text.

    """
    return f"{CustomEmoji.LOADING.value} {text}"


def error(text: str) -> str:
    """Get text prefixed with an error emoji.

    Parameters
    ----------
    text : str
        The text to be prefixed.

    Returns
    -------
    str
        The new message.

    """
    return f"\N{NO ENTRY SIGN} {text}"


def warning(text: str) -> str:
    """Get text prefixed with a warning emoji.

    Parameters
    ----------
    text : str
        The text to be prefixed.

    Returns
    -------
    str
        The new message.

    """
    return f"\N{WARNING SIGN}\N{VARIATION SELECTOR-16} {text}"


def info(text: str) -> str:
    """Get text prefixed with an info emoji.

    Parameters
    ----------
    text : str
        The text to be prefixed.

    Returns
    -------
    str
        The new message.

    """
    return f"\N{INFORMATION SOURCE}\N{VARIATION SELECTOR-16} {text}"


def success(text: str) -> str:
    """Get text prefixed with a success emoji.

    Parameters
    ----------
    text : str
        The text to be prefixed.

    Returns
    -------
    str
        The new message.

    """
    return f"\N{WHITE HEAVY CHECK MARK} {text}"


def question(text: str) -> str:
    """Get text prefixed with a question emoji.

    Parameters
    ----------
    text : str
        The text to be prefixed.

    Returns
    -------
    str
        The new message.

    """
    return f"\N{BLACK QUESTION MARK ORNAMENT}\N{VARIATION SELECTOR-16} {text}"


def bold(text: str, escape_formatting: bool = True) -> str:
    """Get the given text in bold.

    Note: By default, this function will escape ``text`` prior to emboldening.

    Parameters
    ----------
    text : str
        The text to be marked up.
    escape_formatting : `bool`, optional
        Set to :code:`False` to not escape markdown formatting in the text.

    Returns
    -------
    str
        The marked up text.

    """
    return f"**{escape(text, formatting=escape_formatting)}**"


def box(text: str, lang: str = "") -> str:
    """Get the given text in a code block.

    Parameters
    ----------
    text : str
        The text to be marked up.
    lang : `str`, optional
        The syntax highlighting language for the codeblock.

    Returns
    -------
    str
        The marked up text.

    """
    return f"```{lang}\n{text}\n```"


code = box


def inline(text: str) -> str:
    """Get the given text as inline code.

    Parameters
    ----------
    text : str
        The text to be marked up.

    Returns
    -------
    str
        The marked up text.

    """
    if not isinstance(text, str):
        text = str(text)
    if "`" in text:
        return f"``{text}``"
    else:
        return f"`{text}`"


inline_code = inline


def italics(text: str, escape_formatting: bool = True) -> str:
    """Get the given text in italics.

    Note: By default, this function will escape ``text`` prior to italicising.

    Parameters
    ----------
    text : str
        The text to be marked up.
    escape_formatting : `bool`, optional
        Set to :code:`False` to not escape markdown formatting in the text.

    Returns
    -------
    str
        The marked up text.

    """
    return f"*{escape(text, formatting=escape_formatting)}*"


def spoiler(text: str, escape_formatting: bool = True) -> str:
    """Get the given text as a spoiler.

    Note: By default, this function will escape ``text`` prior to making the text a spoiler.

    Parameters
    ----------
    text : str
        The text to be marked up.
    escape_formatting : `bool`, optional
        Set to :code:`False` to not escape markdown formatting in the text.

    Returns
    -------
    str
        The marked up text.

    """
    return f"||{escape(text, formatting=escape_formatting)}||"


def pagify(
    text: str,
    delims: Sequence[str] = ["\n"],
    *,
    priority: bool = False,
    escape_mass_mentions: bool = True,
    shorten_by: int = 8,
    page_length: int = 2000,
) -> Iterator[str]:
    """Generate multiple pages from the given text.

    Note
    ----
    This does not respect code blocks or inline code.

    Parameters
    ----------
    text : str
        The content to pagify and send.
    delims : `sequence` of `str`, optional
        Characters where page breaks will occur. If no delimiters are found
        in a page, the page will break after ``page_length`` characters.
        By default this only contains the newline.

    Other Parameters
    ----------------
    priority : `bool`
        Set to :code:`True` to choose the page break delimiter based on the
        order of ``delims``. Otherwise, the page will always break at the
        last possible delimiter.
    escape_mass_mentions : `bool`
        If :code:`True`, any mass mentions (here or everyone) will be
        silenced.
    shorten_by : `int`
        How much to shorten each page by. Defaults to 8.
    page_length : `int`
        The maximum length of each page. Defaults to 2000.

    Yields
    ------
    `str`
        Pages of the given text.

    """
    in_text = text
    page_length -= shorten_by
    while len(in_text) > page_length:
        this_page_len = page_length
        if escape_mass_mentions:
            this_page_len -= in_text.count("@here", 0, page_length) + in_text.count(
                "@everyone", 0, page_length
            )
        closest_delim = (in_text.rfind(d, 1, this_page_len) for d in delims)
        if priority:
            closest_delim = next((x for x in closest_delim if x > 0), -1)
        else:
            closest_delim = max(closest_delim)
        closest_delim = closest_delim if closest_delim != -1 else this_page_len
        if escape_mass_mentions:
            to_send = escape(in_text[:closest_delim], mass_mentions=True)
        else:
            to_send = in_text[:closest_delim]
        if len(to_send.strip()) > 0:
            yield to_send
        in_text = in_text[closest_delim:]

    if len(in_text.strip()) > 0:
        if escape_mass_mentions:
            yield escape(in_text, mass_mentions=True)
        else:
            yield in_text


def strikethrough(text: str, escape_formatting: bool = True) -> str:
    """Get the given text with a strikethrough.

    Note: By default, this function will escape ``text`` prior to applying a strikethrough.

    Parameters
    ----------
    text : str
        The text to be marked up.
    escape_formatting : `bool`, optional
        Set to :code:`False` to not escape markdown formatting in the text.

    Returns
    -------
    str
        The marked up text.

    """
    return f"~~{escape(text, formatting=escape_formatting)}~~"


def underline(text: str, escape_formatting: bool = True) -> str:
    """Get the given text with an underline.

    Note: By default, this function will escape ``text`` prior to underlining.

    Parameters
    ----------
    text : str
        The text to be marked up.
    escape_formatting : `bool`, optional
        Set to :code:`False` to not escape markdown formatting in the text.

    Returns
    -------
    str
        The marked up text.

    """
    return f"__{escape(text, formatting=escape_formatting)}__"


def quote(text: str) -> str:
    """Quotes the given text.

    Parameters
    ----------
    text : str
        The text to be marked up.

    Returns
    -------
    str
        The marked up text.

    """
    return textwrap.indent(text, "> ", lambda l: True)


def escape(text: str, *, mass_mentions: bool = False, formatting: bool = False) -> str:
    """Get text with all mass mentions or markdown escaped.

    Parameters
    ----------
    text : str
        The text to be escaped.
    mass_mentions : `bool`, optional
        Set to :code:`True` to escape mass mentions in the text.
    formatting : `bool`, optional
        Set to :code:`True` to escape any markdown formatting in the text.

    Returns
    -------
    str
        The escaped text.

    """
    if mass_mentions:
        text = text.replace("@everyone", "@\u200beveryone")
        text = text.replace("@here", "@\u200bhere")
    if formatting:
        text = discord.utils.escape_markdown(text)
    return text


def text_to_file(
    text: str, filename: str = "file.txt", *, spoiler: bool = False, encoding: str = "utf-8"
) -> discord.File:
    """Prepares text to be sent as a file on Discord, without character limit.

    This writes text into a bytes object that can be used for the ``file`` or ``files`` parameters
    of :meth:`discord.abc.Messageable.send`.

    Parameters
    ----------
    text: str
        The text to put in your file.
    filename: str
        The name of the file sent. Defaults to ``file.txt``.
    spoiler: bool
        Whether the attachment is a spoiler. Defaults to ``False``.

    Returns
    -------
    discord.File
        The file containing your text.

    """
    file = BytesIO(text.encode(encoding))
    return discord.File(file, filename, spoiler=spoiler)


def bool_to_emoji(value: bool) -> str:
    """Converts a boolean to an emoji.

    Parameters
    ----------
    value: bool
        The boolean to convert.

    Returns
    -------
    str
        The emoji representing the boolean.

    """
    if value:
        return "✅"
    else:
        return "❌"


def format_numbers(number: int | float | Decimal, ndigits: int = 2) -> str:
    if not float(number).is_integer():
        number = Decimal(number).quantize(Decimal(f"0.{'0' * ndigits}"), rounding=ROUND_HALF_UP)
    return humanize.intcomma(number)
