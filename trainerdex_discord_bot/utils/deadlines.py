from datetime import datetime
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta, MO

from trainerdex_discord_bot.datatypes import GuildConfig
from trainerdex_discord_bot.config import Config

async def get_last_deadline(*, guild_id: int = None, guild_config: GuildConfig = None, timezone: ZoneInfo = None, now: datetime = None) -> datetime:
    if not timezone:
        if not guild_config:
            guild_config = await Config().get_guild(guild_id)
        timezone = ZoneInfo(guild_config.timezone or "UTC")
        
    if not now:
        now = datetime.now(tz=timezone)
    
    if now.tzinfo != timezone:
        now.astimezone(timezone)
        
    this_monday = now + relativedelta(hour=12, minute=0, second=0, microsecond=0, weekday=MO)
    # We want the deadline just gone. If it's before 12pm, we want the deadline from last week.
    if this_monday > now:
        this_monday -= relativedelta(weeks=1)
    
    return this_monday

async def get_next_deadline(*, guild_id: int = None, guild_config: GuildConfig = None, timezone: ZoneInfo = None, now: datetime = None) -> datetime:
    last_deadline = await get_last_deadline(guild_id=guild_id, guild_config=guild_config, timezone=timezone, now=now)
    return last_deadline + relativedelta(weeks=1)