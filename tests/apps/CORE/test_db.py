from core.db.bases import BaseTableModelMixin
from faker import Faker


class TestTableNameMixin:
    def test__tablename__(self, faker: Faker) -> None:
        first_part, second_part = faker.word(), faker.word()
        my_class = type(first_part.capitalize() + second_part.capitalize(), (BaseTableModelMixin,), {})

        result = my_class.__tablename__

        assert result == f"{first_part.lower()}_{second_part.lower()}"
