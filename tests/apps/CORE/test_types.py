import zoneinfo

import pytest
from faker import Faker
from pydantic.datetime_parse import parse_datetime
from pydantic.validators import str_validator
from pytest_mock import MockerFixture

from apps.CORE.helpers import get_utc_timezone
from apps.CORE.types import Email, Phone, StrUUID, Timestamp


class TestStrUUID:
    def test__get_validators__(self) -> None:
        iterator = iter(StrUUID.__get_validators__())

        assert next(iterator) == StrUUID.validate

    def test_validate_uuid(self, faker: Faker) -> None:
        value = faker.uuid4(cast_to=None)

        result = StrUUID.validate(v=value)

        assert result == str(value)

    def test_validate_str(self, faker: Faker) -> None:
        value = faker.uuid4()

        result = StrUUID.validate(v=value)

        assert result == value

    def test_validate_invalid(self, faker: Faker) -> None:
        value = faker.pystr()

        with pytest.raises(ValueError, match="Invalid UUID") as exception_context:
            StrUUID.validate(v=value)

        assert str(exception_context.value) == "Invalid UUID"


class TestTimestamp:
    def test__get_validators__(self) -> None:
        iterator = iter(Timestamp.__get_validators__())

        assert next(iterator) == parse_datetime
        assert next(iterator) == Timestamp.ensure_has_timezone
        assert next(iterator) == Timestamp.to_timestamp

    def test_ensure_has_timezone_no_tz(self, faker: Faker) -> None:
        date_time = faker.date_time(tzinfo=None)
        expected_date_time = date_time.replace(tzinfo=get_utc_timezone())

        result = Timestamp.ensure_has_timezone(v=date_time)

        assert result == expected_date_time

    def test_ensure_has_timezone_no_utc_tz(self, faker: Faker, mocker: MockerFixture) -> None:
        date_time = faker.date_time(tzinfo=zoneinfo.ZoneInfo(key=faker.timezone()))
        expected_result = faker.pystr()
        as_utc_mock = mocker.patch("apps.CORE.types.as_utc", return_value=expected_result)

        result = Timestamp.ensure_has_timezone(v=date_time)

        as_utc_mock.assert_called_with(date_time=date_time)
        assert result == expected_result

    def test_to_timestamp(self, faker: Faker, mocker: MockerFixture) -> None:
        date_time = faker.date_time()
        expected_result = faker.pystr()
        get_timestamp_mock = mocker.patch("apps.CORE.types.get_timestamp", return_value=expected_result)

        result = Timestamp.to_timestamp(v=date_time)

        get_timestamp_mock.assert_called_with(v=date_time)
        assert result == expected_result

    def test__modify_schema__(self, mocker: MockerFixture) -> None:
        field_schema_mock = mocker.MagicMock()

        Timestamp.__modify_schema__(field_schema=field_schema_mock)

        field_schema_mock.update.assert_called_with(
            example=1656080975146.785, examples=[1656080947257.345, 1656080975146]
        )


class TestPhone:
    def test__get_validators__(self) -> None:
        iterator = iter(Phone.__get_validators__())

        assert next(iterator) == Phone.validate

    @pytest.mark.parametrize(argnames="phone", argvalues=["12345678"])
    def test_validate_success(self, phone: str) -> None:
        result = Phone.validate(v=phone)

        assert result == phone

    @pytest.mark.parametrize(
        argnames="phone",
        argvalues=["+12345678", "-12345678", "(123) 45678"],
    )
    def test_validate_error_must_be_digits(self, phone: str) -> None:
        with pytest.raises(ValueError, match="Must be digits"):
            Phone.validate(v=phone)

    @pytest.mark.parametrize(
        argnames="phone",
        argvalues=["012345678"],
    )
    def test_validate_error_invalid_number(self, phone: str) -> None:
        with pytest.raises(ValueError, match="Invalid number"):
            Phone.validate(v=phone)

    def test__modify_schema__(self, mocker: MockerFixture) -> None:
        field_schema_mock = mocker.MagicMock()

        Phone.__modify_schema__(field_schema=field_schema_mock)

        field_schema_mock.update.assert_called_with(
            title="Phone number",
            max_lenght=15,
            example="380978531216",
            examples=["380978531216", "380978531226"],
        )


class TestEmail:
    def test__get_validators__(self) -> None:
        iterator = iter(Email.__get_validators__())

        assert next(iterator) == str_validator
        assert next(iterator) == Email.validate
        assert next(iterator) == Email.lowercase

    @pytest.mark.parametrize(
        argnames=("value", "expected_result"),
        argvalues=(
            ("Test", "test"),
            ("TEST", "test"),
            ("pyTEST", "pytest"),
        ),
    )
    def test_lowercase(self, value: str, expected_result: str) -> None:
        result = Email.lowercase(value=value)

        assert result == expected_result
