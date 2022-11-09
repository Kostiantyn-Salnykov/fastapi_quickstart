import uuid
from typing import Type

from sqlalchemy import select
from sqlalchemy.engine import ChunkedIteratorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from apps.authorization.models import Group, Permission, Role
from apps.CORE.services import AsyncCRUDBase, ModelType
from apps.users.enums import UsersStatuses
from apps.users.models import User


class UsersService(AsyncCRUDBase):
    def __init__(self, model: Type[ModelType]) -> None:
        self.model = model

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
        return result.unique().scalar_one_or_none()  # type: ignore

    async def get_by_email(self, *, session: AsyncSession, email: str) -> User | None:
        statement = select(self.model).where(self.model.email == email)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        return result.scalar_one_or_none()  # type: ignore


users_service = UsersService(model=User)
