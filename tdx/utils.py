from redbot.core.i18n import Translator
from redbot.core.utils import chat_formatting

import trainerdex

_ = Translator("TrainerDex", __file__)

def check_xp(x: trainerdex.Update) -> int:
    if x.xp is None:
        return 0
    return x.xp

def contact_us_on_twitter() -> str:
    return chat_formatting.info(_("If that doesn't look right, please contact us on Twitter. {twitter_handle}")).format(twitter_handle='@TrainerDexApp')
