import uuid

from fastapi import Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import BinaryExpression, UnaryExpression

from apps.CORE.dependencies import BasePagination
from apps.CORE.exceptions import BackendException
from apps.CORE.types import StrOrUUID
from apps.CORE.utils import to_db_encoder
from apps.wishmaster.models import Tag, Wish, WishList
from apps.wishmaster.schemas import (
    WishCreateSchema,
    WishCreateToDBSchema,
    WishListCreateSchema,
    WishListOutSchema,
    WishListToDBCreateSchema,
    WishOutSchema,
    WishUpdateSchema,
    WishUpdateToDBSchema,
)
from apps.wishmaster.services import wish_service, wishlist_service


class WishHandler:
    async def create(self, *, session: AsyncSession, request: Request, data: WishCreateSchema) -> WishOutSchema:
        obj = WishCreateToDBSchema(**data.dict(exclude={"tags"}, exclude_unset=True))
        async with session.begin_nested():
            wish: Wish = Wish(**to_db_encoder(obj=obj))
            if data.tags:
                tags = {Tag(title=tag) for tag in data.tags}
                wish.tags.update(tags)
            session.add(instance=wish)
        await session.refresh(instance=wish)
        return WishOutSchema.from_orm(obj=wish)

    async def read(self, *, session: AsyncSession, request: Request, id: uuid.UUID | str) -> WishOutSchema:
        wish: Wish = await wish_service.read(session=session, id=id, unique=True)
        if not wish:
            raise BackendException(message="Wish not found.", code=status.HTTP_404_NOT_FOUND)
        return WishOutSchema.from_orm(obj=wish)

    async def update(
        self, *, session: AsyncSession, request: Request, id: uuid.UUID | str, data: WishUpdateSchema
    ) -> WishOutSchema:
        obj = WishUpdateToDBSchema(**data.dict(exclude={"tags"}, exclude_unset=True))
        async with session.begin_nested():
            # wish: Wish | None = await wish_service.update(session=session, id=id, obj=obj, unique=True)
            wish: Wish | None = await session.get(entity=Wish, ident=id, populate_existing=True)
            update_dict = to_db_encoder(obj=obj)
            for k, v in update_dict.items():
                setattr(wish, "k", v)
            if data.tags:
                tags = {Tag(title=tag) for tag in data.tags}
                wish.tags.update(tags)
            session.add(instance=wish)
        if not wish:
            raise BackendException(message="Wish not found.", code=status.HTTP_404_NOT_FOUND)
        return WishOutSchema.from_orm(obj=wish)

    async def list(
        self,
        *,
        session: AsyncSession,
        request: Request,
        pagination: BasePagination,
        sorting: list[UnaryExpression],
        filters: list[BinaryExpression],
    ) -> tuple[int, list[Wish]]:
        wishes: list[Wish]
        filters.extend([WishList.owner_id == request.user.id])
        total, wishes = await wish_service.list(
            session=session,
            offset=pagination.offset,
            limit=pagination.limit,
            sorting=sorting,
            filters=filters,
            unique=True,
        )
        return total, wishes

    async def delete(self, *, session: AsyncSession, request: Request, id: uuid.UUID | str, safe: bool = False) -> None:
        result = await wish_service.delete(session=session, id=id)
        if not result.rowcount and not safe:
            raise BackendException(message="Wish not found.", code=status.HTTP_404_NOT_FOUND)
        return None


class WishlistHandler:
    async def create(self, *, session: AsyncSession, request: Request, data: WishListCreateSchema) -> WishListOutSchema:
        data = WishListToDBCreateSchema(**data.dict(), owner_id=request.user.id)
        wishlist: WishList = await wishlist_service.create(session=session, obj=data)
        return WishListOutSchema.from_orm(obj=wishlist)

    async def list(
        self,
        *,
        session: AsyncSession,
        request: Request,
        pagination: BasePagination,
        sorting: list[UnaryExpression],
        filters: list[BinaryExpression],
    ) -> tuple[int, list[WishList]]:
        filters.extend([WishList.owner_id == request.user.id])
        return await wishlist_service.list(
            session=session, sorting=sorting, offset=pagination.offset, limit=pagination.limit, filters=filters
        )

    async def delete(self, *, session: AsyncSession, request: Request, id: StrOrUUID, safe: bool = False) -> None:
        result = await wishlist_service.delete(session=session, id=id, owner_id=request.user.id)
        if not result.rowcount and not safe:
            raise BackendException(message="WishList not found.", code=status.HTTP_404_NOT_FOUND)
        return None


wish_handler = WishHandler()
wishlist_handler = WishlistHandler()
