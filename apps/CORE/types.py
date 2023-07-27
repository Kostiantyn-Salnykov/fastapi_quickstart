import datetime
import re
import typing
import uuid

import phonenumbers
from pydantic import AfterValidator, BaseModel, BeforeValidator, EmailStr, PlainSerializer, WithJsonSchema
from sqlalchemy import Column

from apps.CORE.db import Base
from apps.CORE.helpers import as_utc, get_timestamp, get_utc_timezone

StrOrUUID: typing.TypeAlias = str | uuid.UUID
StrOrNone: typing.TypeAlias = str | None
ListOfAny: typing.TypeAlias = list[typing.Any]
DictStrOfAny: typing.TypeAlias = dict[str, typing.Any]
ModelType = typing.TypeVar("ModelType", bound=Base)
SchemaType = typing.TypeVar("SchemaType", bound=BaseModel)
ModelColumnVar = typing.TypeVar("ModelColumnVar", bound=Column)
ObjectsVar = typing.TypeVar("ObjectsVar", bound=dict[str, None | str | int | float | dict | list])
DatetimeOrNone: typing.TypeAlias = datetime.datetime | None


def validate_uuid(v: StrOrUUID) -> str:
    """Validate UUID object and convert it to string."""
    if isinstance(v, uuid.UUID):
        return str(v)

    try:
        result = uuid.UUID(v)
    except ValueError as error:
        raise ValueError("Invalid UUID") from error
    else:
        return str(result)


StrUUID = typing.Annotated[
    uuid.UUID, PlainSerializer(func=validate_uuid, return_type=str), AfterValidator(func=lambda val: str(val))
]


def validate_timestamp(v: datetime.datetime) -> float:
    """Make from naive datetime a timezone aware (with UTC timezone)."""
    if isinstance(v, float | int):
        # parse value to datetime
        v = datetime.datetime.fromtimestamp(v, tz=get_utc_timezone())

    # if datetime is naive, just replace it to UTC, else convert to utc
    result = v.replace(tzinfo=get_utc_timezone()) if v.tzinfo is None else as_utc(date_time=v)

    return get_timestamp(v=result)


Timestamp = typing.Annotated[
    datetime.datetime | float,
    PlainSerializer(func=lambda val: val, return_type=float),
    BeforeValidator(func=lambda val: validate_timestamp(v=val)),
    WithJsonSchema(
        json_schema={"type": "integer", "examples": [1656080947257.345, 1656080975146], "example": 1656080975146.785},
    ),
]


def validate_phone(v: str) -> str:
    prefix = "+"
    if not re.match(r"^\d{8,15}$", v):
        raise ValueError("Must be digits")
    try:
        v = "".join(digit for digit in v if digit.isdigit())  # format phone (allow only digits)
        v = prefix + v  # add prefix to valid parsing
        parsed_phone = phonenumbers.parse(number=v)
    except phonenumbers.phonenumberutil.NumberParseException as error:
        raise ValueError("Invalid number") from error
    else:
        if phonenumbers.is_possible_number(parsed_phone):  # pragma: no cover
            return v.removeprefix(prefix)

    raise ValueError("Impossible number")  # pragma: no cover


Phone = typing.Annotated[
    str,
    PlainSerializer(func=validate_phone, return_type=str),
    AfterValidator(func=lambda val: validate_phone(v=val)),
    WithJsonSchema(
        json_schema={
            "title": "Phone number",
            "type": "integer",
            "examples": ["380978531216", "380978531226"],
            "example": "380978531216",
            "max_length": 15,
        },
        mode="serialization",
    ),
]


Email = typing.Annotated[EmailStr, AfterValidator(func=lambda val: val.lower())]
