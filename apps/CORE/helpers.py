import datetime
import functools
import typing
import uuid
import zoneinfo
from typing import Any

import orjson
import uuid_extensions
from fastapi.encoders import jsonable_encoder


@functools.lru_cache
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


def id_v7() -> str:
    """Generate UUID with version 7."""
    return uuid_extensions.uuid7str()


def orjson_dumps(v: Any, *, default: typing.Any) -> str:
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode(encoding="utf-8")


def get_timestamp(v: datetime.datetime) -> float:
    """Extract timestamp from datetime object and round for 3 decimal digits."""
    return round(v.timestamp() * 1000, 3)


def proxy_func(x: typing.Any) -> typing.Any:
    """Function that proxies value back (doing nothing)."""
    return x


encodings_dict: dict[typing.Any, typing.Callable[[typing.Any], typing.Any]] = {
    datetime.datetime: proxy_func,  # don't transform datetime object.
    datetime.date: proxy_func,  # don't transform date objects.
}
to_db_encoder = functools.partial(
    jsonable_encoder,
    exclude_unset=True,
    by_alias=False,
    custom_encoder=encodings_dict,  # override `jsonable_encoder` default behaviour.
)
