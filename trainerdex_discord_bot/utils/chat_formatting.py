import textwrap
from io import BytesIO
from typing import Iterator, Optional, Sequence

import discord
from babel.lists import format_list as babel_list


def error(text: str) -> str:
    return f"\N{NO ENTRY SIGN} {text}"


def warning(text: str) -> str:
    return f"\N{WARNING SIGN}\N{VARIATION SELECTOR-16} {text}"


def info(text: str) -> str:
    return f"\N{INFORMATION SOURCE}\N{VARIATION SELECTOR-16} {text}"


def loading(text: str) -> str:
    emoji: str = "<a:loading:471298325904359434>"
    return f"{emoji} {text}"


def success(text: str) -> str:
    return f"\N{WHITE HEAVY CHECK MARK} {text}"


def question(text: str) -> str:
    return f"\N{BLACK QUESTION MARK ORNAMENT}\N{VARIATION SELECTOR-16} {text}"


def box(text: str, lang: str = "") -> str:
    return f"```{lang}\n{text}\n```"


def spoiler(text: str, escape_formatting: bool = True) -> str:
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
    return f"~~{escape(text, formatting=escape_formatting)}~~"


def underline(text: str, escape_formatting: bool = True) -> str:
    return f"__{escape(text, formatting=escape_formatting)}__"


def quote(text: str) -> str:
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


def humanize_list(
    items: Sequence[str], *, locale: Optional[str] = None, style: str = "standard"
) -> str:
    """Get comma-separated list, with the last element joined with *and*.

    Parameters
    ----------
    items : Sequence[str]
        The items of the list to join together.
    locale : Optional[str]
        The locale to convert, if not specified it defaults to the bot's locale.
    style : str
        The style to format the list with.

        Note: Not all styles are necessarily available in all locales,
        see documentation of `babel.lists.format_list` for more details.

        standard
            A typical 'and' list for arbitrary placeholders.
            eg. "January, February, and March"
        standard-short
             A short version of a 'and' list, suitable for use with short or
             abbreviated placeholder values.
             eg. "Jan., Feb., and Mar."
        or
            A typical 'or' list for arbitrary placeholders.
            eg. "January, February, or March"
        or-short
            A short version of an 'or' list.
            eg. "Jan., Feb., or Mar."
        unit
            A list suitable for wide units.
            eg. "3 feet, 7 inches"
        unit-short
            A list suitable for short units
            eg. "3 ft, 7 in"
        unit-narrow
            A list suitable for narrow units, where space on the screen is very limited.
            eg. "3′ 7″"

    Raises
    ------
    ValueError
        The locale does not support the specified style.

    Examples
    --------
    .. testsetup::

        from redbot.core.utils.chat_formatting import humanize_list

    .. doctest::

        >>> humanize_list(['One', 'Two', 'Three'])
        'One, Two, and Three'
        >>> humanize_list(['One'])
        'One'
        >>> humanize_list(['omena', 'peruna', 'aplari'], style='or', locale='fi')
        'omena, peruna tai aplari'

    """

    return babel_list(items, style=style)


def text_to_file(
    text: str, filename: str = "file.txt", *, spoiler: bool = False, encoding: str = "utf-8"
):
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
