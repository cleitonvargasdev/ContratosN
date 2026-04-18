from datetime import UTC, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.config import settings


def get_local_timezone() -> tzinfo:
    try:
        return ZoneInfo(settings.app_timezone)
    except ZoneInfoNotFoundError:
        return UTC