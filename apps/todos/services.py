from sqlalchemy import func, select
from sqlalchemy.engine import ChunkedIteratorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import UnaryExpression

from apps.CORE.services import AsyncCRUDBase
from apps.todos.models import ToDo


class ToDoCRUDBase(AsyncCRUDBase):
    async def list(
        self,
        *,
        session: AsyncSession,
        sorting: list[UnaryExpression],
        offset: int = 0,
        limit: int = 100,
        filters: dict | None = None  # TODO: Add dynamic filtering system
    ) -> tuple[int, list[ToDo]]:
        select_statement = select(self.model)
        if filters:
            select_statement = select_statement.filter_by(**filters)
        select_statement = (
            select_statement.order_by(*sorting).offset(offset).limit(limit).execution_options(populate_existing=True)
        )

        async with session.begin_nested():
            count_result: ChunkedIteratorResult = await session.execute(statement=select(func.count(self.model.id)))
            select_result: ChunkedIteratorResult = await session.execute(statement=select_statement)

        total: int = count_result.scalar()
        objects: list[ToDo] = select_result.scalars().all()
        return total, objects


to_do_service = ToDoCRUDBase(model=ToDo)
