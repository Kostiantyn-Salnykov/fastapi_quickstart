import uuid

from fastapi import Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.CORE.dependencies import BasePagination
from apps.CORE.exceptions import BackendException
from apps.CORE.schemas import PaginationOutSchema
from apps.todos.models import ToDo
from apps.todos.schemas import ToDoCreateSchema, ToDoOutSchema, ToDoUpdateSchema
from apps.todos.services import to_do_service


class ToDoHandler:
    async def create(self, *, session: AsyncSession, request: Request, data: ToDoCreateSchema) -> ToDoOutSchema:
        to_do: ToDo = await to_do_service.create(session=session, obj=data)
        return ToDoOutSchema.from_orm(obj=to_do)

    async def read(self, *, session: AsyncSession, request: Request, id: uuid.UUID | str) -> ToDoOutSchema:
        to_do: ToDo = await to_do_service.read(session=session, id=id)
        if not to_do:
            raise BackendException(message="ToDo not found.", code=status.HTTP_404_NOT_FOUND)
        return ToDoOutSchema.from_orm(obj=to_do)

    async def update(
        self, *, session: AsyncSession, request: Request, id: uuid.UUID | str, data: ToDoUpdateSchema
    ) -> ToDoOutSchema:
        to_do: ToDo = await to_do_service.update(session=session, id=id, obj=data)
        if not to_do:
            raise BackendException(message="ToDo not found.", code=status.HTTP_404_NOT_FOUND)
        return ToDoOutSchema.from_orm(obj=to_do)

    async def list(
        self,
        *,
        session: AsyncSession,
        request: Request,
        pagination: BasePagination,
        sorting,
        filters: dict | None = None
    ) -> PaginationOutSchema:
        total, objects = await to_do_service.list(
            session=session, offset=pagination.offset, limit=pagination.limit, sorting=sorting, filters=filters
        )
        return BasePagination.get_paginated_response(
            pagination=pagination, request=request, objects=objects, schema=ToDoOutSchema, total=total
        )

    async def delete(self, *, session: AsyncSession, request: Request, id: uuid.UUID | str, safe: bool = False) -> None:
        result = await to_do_service.delete(session=session, id=id)
        if not result.rowcount and not safe:
            raise BackendException(message="ToDo not found.", code=status.HTTP_404_NOT_FOUND)
        return None


to_do_handler = ToDoHandler()
