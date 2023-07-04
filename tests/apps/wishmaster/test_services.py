import datetime
import uuid

import pytest
from faker import Faker
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from apps.wishmaster.enums import WishStatuses
from apps.wishmaster.models import Wish
from apps.wishmaster.schemas import WishCreateSchema, WishResponseSchema, WishUpdateSchema
from apps.wishmaster.services import WishCRUD


class _TestWishCRUDBase:
    @classmethod
    def setup_class(cls):
        cls.service = WishCRUD(model=Wish)

    async def clear_wishes(self, session: AsyncSession):
        await session.execute(statement=delete(Wish))
        await session.commit()

    @staticmethod
    def check_uuid(field, expected_type: type = uuid.UUID) -> None:
        assert isinstance(field, expected_type)

    @staticmethod
    def check_datetime(field, expected_type: type = datetime.datetime) -> None:
        assert isinstance(field, expected_type)

    def check_defaults(self, obj):
        self.check_uuid(field=obj.id)
        self.check_datetime(field=obj.created_at)
        self.check_datetime(field=obj.updated_at)

    async def test_list(self, faker: Faker, db_session: AsyncSession):
        await self.clear_wishes(session=db_session)
        wishes = await WishSchemaFactory.create_batch_async(size=faker.pyint(min_value=3, max_value=5))

        total, todos_list = await self.service.list(session=db_session, sorting=[])

        assert total == len(wishes)
        assert [todo.__repr__() for todo in todos_list] == [todo.__repr__() for todo in wishes]

    async def test_create(self, db_session: AsyncSession) -> None:
        equal_fields = {"text", "description"}
        wish: WishCreateSchema = WishSchemaFactory.build()

        result = await self.service.create(session=db_session, obj=wish)

        assert isinstance(result, Wish)
        result_schema = WishResponseSchema.from_orm(obj=result)
        assert result_schema.dict(include=equal_fields) == wish.dict(include=equal_fields)
        self.check_defaults(obj=result)

    async def test_read(self, db_session: AsyncSession) -> None:
        wish: Wish = await WishSchemaFactory.create_async()

        result: Wish = await self.service.read(session=db_session, id=wish.id)

        assert isinstance(result, Wish)
        assert result.id == wish.id
        assert str(result) == str(wish)

    async def test_read_none(self, faker: Faker, db_session: AsyncSession) -> None:
        fake_uuid = faker.uuid4(cast_to=None)

        result = await self.service.read(session=db_session, id=fake_uuid)

        assert result is None

    @pytest.mark.parametrize(
        argnames="status", argvalues=[WishStatuses.IN_PROGRESS, WishStatuses.ARCHIVED, WishStatuses.COMPLETED]
    )
    async def test_update(self, faker: Faker, db_session: AsyncSession, status: WishStatuses) -> None:
        wish: Wish = await WishSchemaFactory.create_async()
        new_title, new_description = faker.pystr(), faker.pystr()
        assert wish.title != new_title
        assert wish.description != new_description
        assert wish.status != status

        result: Wish = await self.service.update(
            session=db_session,
            id=wish.id,
            obj=WishUpdateSchema(title=new_title, description=new_description, status=status),
        )

        assert result.title == new_title
        assert result.description == new_description
        assert result.status == status

    async def test_delete(self, db_session: AsyncSession) -> None:
        wish: Wish = await WishSchemaFactory.create_async()

        result = await self.service.delete(session=db_session, id=wish.id)
        assert result.rowcount == 1  # deleted one object from db

        result2 = await self.service.delete(session=db_session, id=wish.id)
        assert result2.rowcount == 0  # already deleted
