import typing
import uuid

from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import UnaryExpression

from apps.CORE.dependencies import BasePagination, BaseSorting, get_async_session
from apps.CORE.schemas import JSENDOutSchema
from apps.todos.handlers import to_do_handler
from apps.todos.models import ToDo
from apps.todos.schemas import ToDoCreateSchema, ToDoListOutSchema, ToDoOutSchema, ToDoUpdateSchema

to_do_router = APIRouter(prefix="/to_do", tags=["ToDo"])


@to_do_router.post(path="/", response_model=JSENDOutSchema[ToDoOutSchema])
async def create_to_do(
    request: Request, data: ToDoCreateSchema, session: AsyncSession = Depends(get_async_session)
) -> JSENDOutSchema:
    return JSENDOutSchema[ToDoOutSchema](
        data=await to_do_handler.create(session=session, request=request, data=data),
        message="Created ToDo details.",
    )


@to_do_router.get(path="/{id}/", response_model=JSENDOutSchema[ToDoOutSchema])
async def read_to_do(
    request: Request, id: uuid.UUID = Path(), session: AsyncSession = Depends(get_async_session)
) -> JSENDOutSchema:
    return JSENDOutSchema[ToDoOutSchema](
        data=await to_do_handler.read(session=session, request=request, id=id),
        message="ToDo details.",
    )


@to_do_router.patch(path="/{id}/", name="update_to_do", response_model=JSENDOutSchema[ToDoOutSchema])
async def update_to_do(
    request: Request, data: ToDoUpdateSchema, id: uuid.UUID = Path(), session: AsyncSession = Depends(get_async_session)
) -> JSENDOutSchema:
    return JSENDOutSchema[ToDoOutSchema](
        data=await to_do_handler.update(session=session, request=request, id=id, data=data),
        message="Updated ToDo details.",
    )


@to_do_router.get(path="/", name="list_to_do", response_model=ToDoListOutSchema)
async def list_to_do(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    pagination: BasePagination = Depends(BasePagination()),
    sorting: list[UnaryExpression] = Depends(BaseSorting(model=ToDo, available_columns=[ToDo.created_at, ToDo.title])),
) -> dict[str, typing.Any]:
    return {
        "data": await to_do_handler.list(session=session, request=request, pagination=pagination, sorting=sorting),
        "message": "Paginated list of ToDo objects.",
    }


@to_do_router.delete(path="/{id}/", response_model=JSENDOutSchema)
async def delete_to_do(
    request: Request,
    id: uuid.UUID = Path(),
    session: AsyncSession = Depends(get_async_session),
) -> JSENDOutSchema:
    await to_do_handler.delete(session=session, request=request, id=id)
    return JSENDOutSchema(data=None, message="ToDo deleted successfully.")
