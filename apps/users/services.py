import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import ChunkedIteratorResult, CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from apps.CORE.helpers import to_db_encoder
from apps.CORE.repositories import BaseCoreRepository
from apps.CORE.tables import Group, Permission, Role, User
from apps.users.enums import UserStatuses
from apps.users.schemas.requests import UserCreateSchema

__all__ = ("users_service",)


class UsersService(BaseCoreRepository):
    async def create(self, *, session: AsyncSession, obj: UserCreateSchema) -> User:
        obj.status = UserStatuses.CONFIRMED  # Automatically activates User!!!
        async with session.begin_nested():
            statement = insert(self.model).values(**to_db_encoder(obj=obj))
            result: CursorResult = await session.execute(statement=statement)
            return await self.get_with_grp(session=session, id=result.inserted_primary_key[0])

    async def get_with_grp(self, *, session: AsyncSession, id: uuid.UUID) -> User | None:
        statement = (
            select(self.model)
            .where(self.model.id == id)
            .where(self.model.status.in_((UserStatuses.CONFIRMED, UserStatuses.FORCE_CHANGE_PASSWORD)))
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
