import datetime
import uuid
import zoneinfo

import orjson
from faker import Faker
from pydantic.json import timedelta_isoformat

from apps.CORE.helpers import get_timestamp
from apps.CORE.schemas.responses import BaseResponseSchema
from apps.CORE.types import Timestamp


class TestBaseOutSchema:
    class CheckSchema(BaseResponseSchema):
        field_datetime: datetime.datetime
        field_timestamp: Timestamp
        field_timedelta: datetime.timedelta
        field_uuid: uuid.UUID

    def test_config(self, faker: Faker):
        date_time, date_time_2 = faker.date_time(), faker.date_time(tzinfo=zoneinfo.ZoneInfo(key="UTC"))
        time_delta = faker.time_delta(datetime.timedelta(seconds=faker.pyint()))
        fake_uuid = faker.uuid4(cast_to=None)
        schema = self.CheckSchema(
            field_datetime=date_time, field_timestamp=date_time_2, field_timedelta=time_delta, field_uuid=fake_uuid
        )
        excepted_dict = {
            "field_datetime": date_time,
            "field_timestamp": get_timestamp(v=date_time_2),
            "field_timedelta": time_delta,
            "field_uuid": fake_uuid,
        }
        expected_converted_json_dict = {
            "field_datetime": date_time.isoformat(),
            "field_timestamp": get_timestamp(v=date_time_2),
            "field_timedelta": timedelta_isoformat(time_delta),
            "field_uuid": str(fake_uuid),
        }

        dict_result = schema.dict()
        json_result = schema.json()
        converted_json_dict = orjson.loads(json_result)

        assert dict_result == excepted_dict
        assert isinstance(json_result, str)
        assert converted_json_dict == expected_converted_json_dict
