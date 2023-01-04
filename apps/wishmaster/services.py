from sqlalchemy import distinct, func, select
from sqlalchemy.engine import ChunkedIteratorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, contains_eager, joinedload, selectinload, subqueryload
from sqlalchemy.sql.elements import BinaryExpression, UnaryExpression

from apps.CORE.services import AsyncCRUDBase
from apps.CORE.types import StrOrUUID
from apps.users.models import User
from apps.wishmaster.models import Category, Tag, Wish, WishList


class WishCRUD(AsyncCRUDBase):
    async def list(
        self,
        *,
        session: AsyncSession,
        sorting: list[UnaryExpression],
        offset: int = 0,
        limit: int = 100,
        filters: list[BinaryExpression] | None = None,
        unique: bool = False
    ) -> tuple[int, list[Wish]]:
        select_statement = (
            select(self.model)
            .join(WishList)
            .where(*filters or {})
            .order_by(*sorting)
            .offset(offset)
            .limit(limit)
            .execution_options(populate_existing=True)
        )
        count_statement = (
            select(func.count(self.model.id))
            .select_from(self.model)
            .where(Wish.wishlist_id == WishList.id)
            .where(*filters or {})
        )

        async with session.begin_nested():
            count_result: ChunkedIteratorResult = await session.execute(statement=count_statement)
            select_result: ChunkedIteratorResult = await session.execute(statement=select_statement)

        total: int = count_result.scalar()  # number of counted results.
        select_result.unique() if unique else ...  # Logic for M2M joins
        objects: list[Wish] = select_result.scalars().all()
        return total, objects


class WishListCRUD(AsyncCRUDBase):
    async def list(
        self,
        *,
        session: AsyncSession,
        sorting: list[UnaryExpression],
        offset: int = 0,
        limit: int = 100,
        filters: list[BinaryExpression] | None = None,
        unique: bool = True
    ) -> tuple[int, list[WishList]]:
        select_statement = (
            select(self.model)
            .join(Wish, onclause=WishList.id == Wish.wishlist_id, isouter=True)
            .options(joinedload(WishList.wishes))
        )
        if filters:
            select_statement = select_statement.where(*filters)
        select_statement = (
            select_statement.order_by(*sorting).offset(offset).limit(limit).execution_options(populate_existing=True)
        )
        print(select_statement)
        count_statement = select(func.count(self.model.id)).select_from(self.model).where(*filters or {})

        async with session.begin_nested():
            count_result: ChunkedIteratorResult = await session.execute(statement=count_statement)
            select_result: ChunkedIteratorResult = await session.execute(statement=select_statement)

        total: int = count_result.scalar()  # number of counted results.
        select_result.unique() if unique else ...  # Logic for M2M joins
        objects: list[WishList] = select_result.scalars().all()
        return total, objects


class TagCRUD(AsyncCRUDBase):
    ...


class CategoryCRUD(AsyncCRUDBase):
    ...


wish_service = WishCRUD(model=Wish)
wishlist_service = WishListCRUD(model=WishList)
tag_service = TagCRUD(model=Tag)
category_service = CategoryCRUD(model=Category)
