import datetime
import uuid
import zoneinfo

import orjson
from faker import Faker

from apps.CORE.custom_types import Timestamp
from apps.CORE.helpers import get_timestamp
from apps.CORE.schemas.responses import BaseResponseSchema


class TestBaseOutSchema:
    class CheckSchema(BaseResponseSchema):
        field_datetime: datetime.datetime
        field_timestamp: Timestamp
        field_timedelta: datetime.timedelta
        field_uuid: uuid.UUID

    def test_config(self, faker: Faker) -> None:
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

        def timedelta_to_iso_string(timedelta_obj: datetime.timedelta) -> str:
            # Step 1: Get the total number of seconds from the timedelta object
            total_seconds = timedelta_obj.total_seconds()

            # Step 2: Format the total seconds into the ISO 8601 duration format
            # For positive durations: PnYnMnDTnHnMnS
            # For negative durations: -PnYnMnDTnHnMnS
            # where n is the number of years, months, days, hours, minutes, or seconds.
            # Note that ISO 8601 doesn't include months, so they will be converted to days.
            sign = "-" if total_seconds < 0 else ""
            total_seconds = abs(total_seconds)
            total_seconds // (24 * 3600)
            (total_seconds % (24 * 3600)) // 3600
            (total_seconds % 3600) // 60
            total_seconds % 60

            # iso_string = f"{sign}P{int(days)}DT{int(hours)}H{int(minutes)}M{int(seconds)}S"
            iso_string = f"{sign}PT{int(total_seconds)}S"
            return iso_string

        expected_converted_json_dict = {
            "field_datetime": date_time.isoformat(),
            "field_timestamp": get_timestamp(v=date_time_2),
            "field_timedelta": timedelta_to_iso_string(timedelta_obj=time_delta),
            "field_uuid": str(fake_uuid),
        }

        dict_result = schema.model_dump(mode="python")
        json_result = schema.model_dump_json()
        converted_json_dict = orjson.loads(json_result)

        assert dict_result == excepted_dict
        assert isinstance(json_result, str)
        assert converted_json_dict == expected_converted_json_dict
