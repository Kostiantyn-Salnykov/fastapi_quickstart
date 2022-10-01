import datetime
import uuid
import zoneinfo

import pytest
from faker import Faker
from pytest_mock import MockerFixture

from apps.CORE.utils import as_utc, get_timestamp, get_utc_timezone, id_v1, id_v4, orjson_dumps, utc_now


def test_get_utc_timezone():
    result = get_utc_timezone()

    assert result == zoneinfo.ZoneInfo(key="UTC")
    assert isinstance(result, zoneinfo.ZoneInfo)


def test_utc_now(faker: Faker, mocker: MockerFixture):
    expected_datetime: datetime.datetime = faker.date_time(tzinfo=zoneinfo.ZoneInfo(key="UTC"))
    date_time_mock = mocker.patch("apps.CORE.utils.datetime")
    date_time_mock.datetime.now.return_value = expected_datetime

    result = utc_now()

    assert result == expected_datetime
    assert result.tzinfo == zoneinfo.ZoneInfo(key="UTC")


def test_as_utc(faker: Faker):
    input_date_time = faker.date_time(tzinfo=zoneinfo.ZoneInfo(key=faker.timezone()))

    result = as_utc(date_time=input_date_time)

    assert result == input_date_time
    assert result.tzinfo == zoneinfo.ZoneInfo(key="UTC")


def test_id_v1(mocker: MockerFixture):
    expected_uuid = uuid.uuid1()
    uuid_mock = mocker.patch("apps.CORE.utils.uuid")
    uuid_mock.uuid1.return_value = expected_uuid

    result = id_v1()

    assert result == str(expected_uuid)
    assert uuid.UUID(result).time == expected_uuid.time


def test_id_v4(mocker: MockerFixture):
    expected_uuid = uuid.uuid1()
    uuid_mock = mocker.patch("apps.CORE.utils.uuid")
    uuid_mock.uuid4.return_value = expected_uuid

    result = id_v4()

    assert result == str(expected_uuid)


@pytest.mark.parametrize(
    argnames=["data", "expected_result"],
    argvalues=(
        ("test", '"test"'),
        ([0, 1], "[0,1]"),
        ({"1": 1, "2": 2}, '{"1":1,"2":2}'),
        (1, "1"),
        (3.14, "3.14"),
        (True, "true"),
        (False, "false"),
        (None, "null"),
    ),
)
def test_orjson_dumps(data, expected_result):
    result = orjson_dumps(v=data, default=None)

    assert isinstance(result, str)
    assert result == expected_result


def test_get_timestamp(faker: Faker):
    date_time = faker.date_time()

    result = get_timestamp(v=date_time)

    assert result == round(date_time.timestamp() * 1000, 3)
