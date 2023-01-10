import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import ChunkedIteratorResult, CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from apps.CORE.repositories import BaseCoreRepository
from apps.CORE.tables import Group, Permission, Role, User
from apps.CORE.utils import to_db_encoder
from apps.users.enums import UsersStatuses
from apps.users.schemas import UserCreateSchema

__all__ = ("users_service",)


class UsersService(BaseCoreRepository):
    async def create(self, *, session: AsyncSession, obj: UserCreateSchema, unique: bool = False) -> User:
        obj.status = UsersStatuses.CONFIRMED  # Automatically activates User!!!
        obj_in_data = to_db_encoder(obj=obj)
        async with session.begin_nested():
            statement = insert(self.model).values(**obj_in_data)
            result: CursorResult = await session.execute(statement=statement)
            inserted_id: uuid.UUID = result.inserted_primary_key[0]
            user: User = await self.get_with_authorization(session=session, id=inserted_id)
        return user

    async def get_with_authorization(self, *, session: AsyncSession, id: uuid.UUID) -> User | None:
        statement = (
            select(self.model)
            .where(self.model.id == id)
            .where(self.model.status.in_((UsersStatuses.CONFIRMED, UsersStatuses.FORCE_CHANGE_PASSWORD)))
            .join(Group, User.groups, isouter=True)
            .join(Role, User.roles, isouter=True)
            .join(Permission, User.permissions, isouter=True)
            .options(contains_eager(User.groups), contains_eager(User.roles), contains_eager(User.permissions))
        )
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        return result.unique().scalar_one_or_none()

    async def get_by_email(self, *, session: AsyncSession, email: str) -> User | None:
        statement = select(self.model).where(self.model.email == email)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        return result.scalar_one_or_none()


users_service = UsersService(model=User)
