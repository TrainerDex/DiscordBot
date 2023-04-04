from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from yarl import URL


def google_calendar_link_for_datetime(dt: datetime) -> str:
    """Return a Google Calendar link for a datetime."""

    path = URL("http://www.google.com/calendar/event")

    # Format date as YYYYMMDDTHHMMSSZ
    dt = dt.astimezone(ZoneInfo("UTC"))

    start_time = (dt - timedelta(minutes=15)).strftime("%Y%m%dT%H%M%SZ")
    end_time = dt.strftime("%Y%m%dT%H%M%SZ")

    return path % {
        "action": "TEMPLATE",
        "text": f"TrainerDex Leaderboards Deadline: Week {dt.strftime('%V')}",
        "dates": f"{start_time}/{end_time}",
        "details": "The deadline for submitting your screenshots for the TrainerDex Leaderboards for this week.",
        "location": "https://trainerdex.app/new/",
    }
