import datetime
import zoneinfo

import pytest
from faker import Faker
from pydantic import TypeAdapter
from pytest_mock import MockerFixture

from apps.CORE.helpers import get_timestamp, get_utc_timezone
from apps.CORE.types import Email, Phone, StrUUID, Timestamp


class TestTimestamp:
    @pytest.mark.debug()
    def test_timestamp(self) -> None:
        ta = TypeAdapter(type=Timestamp)
        value1 = 1690402796.119  # TODO: 119
        value1_dt = datetime.datetime.utcfromtimestamp(value1)

        res = ta.dump_json(value1_dt)
        res2 = ta.dump_python(value1_dt, mode="python")
        res3 = ta.dump_python(value1_dt, mode="json")
        res4 = ta.validate_python(value1_dt)
        res5 = ta.validate_json(str(value1))

        print(True)
