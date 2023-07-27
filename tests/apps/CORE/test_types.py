import datetime

import pytest
from pydantic import TypeAdapter

from apps.CORE.helpers import get_utc_timezone
from apps.CORE.types import Timestamp


class TestTimestamp:
    @pytest.mark.debug()
    def test_timestamp(self) -> None:
        ta = TypeAdapter(type=Timestamp)
        value1 = 1690402796.119  # TODO: 119
        value1_dt = datetime.datetime.fromtimestamp(value1, tz=get_utc_timezone())

        ta.dump_json(value1_dt)
        ta.dump_python(value1_dt, mode="python")
        ta.dump_python(value1_dt, mode="json")
        ta.validate_python(value1_dt)
        ta.validate_json(str(value1))

        print(True)
