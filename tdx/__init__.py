"""
Official TrainerDex Discord Bot
-------------------------------

TrainerDex cog for Red-DiscordBot 3

:copyright: (c) 2020 TrainerDex/TurnrDev
:licence: GNU-GPL3, see LICENSE for more details

"""

from .version import get_version

VERSION = (2020, 51, 0, "alpha", 0)

__version__ = get_version(VERSION)
__red_end_user_data_statement__ = """We use several terms in this document which could be considered ambiguous so I would like to clear these up:
 * the Website - any website hosted on the trainerdex.co.uk domain or any subdomains thereof
 * the Discord Bot - Our official bot instance, TrainerDex#8522, on Discord, or any third party instances that may or may not launch in the future.

By signing up to TrainerDex through any of the various methods such as; the Website, the Discord Bot or any of our other apps, present and future, you are agreeing to these Terms of Service. These terms of service are subject to change at any time.

We, TrainerDex, have the right to save and store screenshots of your stats for future audits and verification. We reserve the right to deny a user access to TrainerDex at any time, however, we will always try to provide the reason to the user.

The following rules/terms are in place and violation of these rules can result in termination of your profile and a permanent ban from the service;

 * No use of tools and/or apps to falsify your location in Pokémon Go
 * No use of any tools or software or other methods to falsify your screenshots before submitting them.
 * No submitting anybody else’s screenshots as your own
 * No knowingly submitting false data to TrainerDex

We endeavour to be open with data. We have a public API for information such as your Pokémon Go profile data. As such, your data may be used on third party tools such as PokeNav.

The types of information we may store on you include;
 * Various datapoints about your Pokémon Go profile, including username, team, start date and any of the badges information provided to us
 * Your first name, if provided
 * Your email address, if provided
 * Your Discord UID, if provided via the Website or via using the Discord Bot
 * Your Twitter UID, if provided via the Website
 * Your Facebook name, if provided via the Website

It is within your right to request to be removed from TrainerDex or have your information hidden at any time. However, we are not responsible for third party services caching your public data.

To request removal or to be hidden from TrainerDex, email <jay@trainerdex.co.uk> or message TurnrDev#0117 on Discord.
"""

from redbot.core.bot import Red

from .trainerdex import TrainerDex


async def setup(bot: Red) -> None:
    bot.add_cog(TrainerDex(bot))
