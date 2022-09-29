import datetime
import functools
import uuid
import zoneinfo


@functools.lru_cache()
def get_utc_timezone() -> zoneinfo.ZoneInfo:
    """Return UTC zone info."""
    return zoneinfo.ZoneInfo(key="UTC")


def utc_now() -> datetime.datetime:
    """Return current datetime with UTC zone info."""
    return datetime.datetime.now(tz=get_utc_timezone())


def as_utc(date_time: datetime.datetime) -> datetime.datetime:
    """Get datetime object and convert it to datetime with UTC zone info."""
    return date_time.astimezone(tz=get_utc_timezone())


def id_v1() -> str:
    """Generate UUID with version 1 (can extract created_at datetime)."""
    return str(uuid.uuid1())


def id_v4() -> str:
    """Generate UUID with version 4."""
    return str(uuid.uuid4())


def construct_pagination(objects: list, schema, pagination):
    ...
