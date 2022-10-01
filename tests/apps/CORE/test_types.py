import pytest
from faker import Faker

from apps.CORE.types import StrUUID


class TestStrUUID:
    def test_validate_uuid(self, faker: Faker):
        value = faker.uuid4(cast_to=None)

        result = StrUUID.validate(v=value)

        assert result == str(value)

    def test_validate_str(self, faker: Faker):
        value = faker.uuid4()

        result = StrUUID.validate(v=value)

        assert result == value

    def test_validate_invalid(self, faker: Faker):
        value = faker.pystr()

        with pytest.raises(ValueError) as exception_context:
            StrUUID.validate(v=value)

        assert str(exception_context.value) == "Invalid UUID"
