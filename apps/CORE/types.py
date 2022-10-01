import datetime
import re
import typing
import uuid

import phonenumbers
from pydantic import EmailStr
from pydantic.datetime_parse import parse_datetime

from apps.CORE.utils import as_utc, get_timestamp, get_utc_timezone


class StrUUID(str):
    @classmethod
    def __get_validators__(cls):
        """Run validate class method."""
        yield cls.validate

    @classmethod
    def validate(cls, v) -> str:
        if isinstance(v, uuid.UUID):
            return str(v)

        try:
            result = uuid.UUID(v)
        except ValueError as error:
            raise ValueError("Invalid UUID") from error
        else:
            return str(result)


class Timestamp(float):
    @classmethod
    def __get_validators__(cls):
        """Run validation class methods."""
        yield parse_datetime
        yield cls.ensure_has_timezone
        yield cls.to_timestamp

    @classmethod
    def ensure_has_timezone(cls, v: datetime.datetime) -> datetime.datetime:
        """Make naive datetime a timezone aware (with UTC timezone)."""
        # if datetime is naive, just replace it to UTC
        if v.tzinfo is None:
            return v.replace(tzinfo=get_utc_timezone())
        # else convert to utc
        return as_utc(date_time=v)

    @classmethod
    def to_timestamp(cls, v: datetime.datetime) -> float | int:
        return get_timestamp(v=v)

    @classmethod
    def __modify_schema__(cls, field_schema: dict) -> None:
        """Update type OpenAPIv3 schema."""
        field_schema.update(
            example=1656080975146.785,
            examples=[1656080947257.345, 1656080975146],
        )


class Phone(str):
    @classmethod
    def __get_validators__(cls):
        """Run validate class method."""
        yield cls.validate

    @classmethod
    def validate(cls, v: str) -> str:
        PREFIX = "+"
        if not re.match(r"^\d{8,15}$", v):
            raise ValueError("Mast be digits")
        try:
            v = "".join((digit for digit in v if digit.isdigit()))  # format phone (allow only digits)
            v = PREFIX + v  # add prefix to valid parsing
            parsed_phone = phonenumbers.parse(number=v)
        except phonenumbers.phonenumberutil.NumberParseException as error:
            raise ValueError("Invalid number") from error
        else:
            if phonenumbers.is_possible_number(parsed_phone):
                return v.removeprefix(PREFIX)

        raise ValueError("Impossible number")

    @classmethod
    def __modify_schema__(cls, field_schema: dict) -> None:
        """Update type OpenAPIv3 schema."""
        field_schema.update(
            title="Phone number",
            max_lenght=15,
            example="380978531216",
            examples=["380978531216", "380978531226"],
        )


class Email(EmailStr):
    """Lowercase version of Pydantic EmailStr field type."""

    @classmethod
    def __get_validators__(cls) -> typing.Generator[typing.Callable, None, None]:
        """Add extra validator to Pydantic EmailStr field."""
        yield from super().__get_validators__()
        yield cls.lowercase

    @classmethod
    def lowercase(cls, value: str) -> str:
        """Lowercase email value.

        Returns:
            value (str): lowercase value of email.
        """
        return value.lower()
