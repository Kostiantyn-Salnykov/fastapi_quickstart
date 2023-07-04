from faker import Faker

from apps.CORE.db import BaseTableModelMixin


class TestTableNameMixin:
    def test__tablename__(self, faker: Faker):
        first_part, second_part = faker.word(), faker.word()
        my_class = type(first_part.capitalize() + second_part.capitalize(), (BaseTableModelMixin,), {})

        result = my_class.__tablename__

        assert result == f"{first_part.lower()}_{second_part.lower()}"
