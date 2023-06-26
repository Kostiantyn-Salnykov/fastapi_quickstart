import typing
import uuid

from fastapi import APIRouter, Body, Depends, Path, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import UnaryExpression

from apps.authorization.dependencies import bearer_auth
from apps.authorization.handlers import groups_handler, permissions_handler, roles_handler
from apps.authorization.schemas import (
    GroupCreateSchema,
    GroupListOutSchema,
    GroupOutSchema,
    GroupUpdateSchema,
    PermissionListOutSchema,
    PermissionOutSchema,
    RoleCreateSchema,
    RoleListOutSchema,
    RoleOutSchema,
)
from apps.CORE.deps import get_async_session
from apps.CORE.deps.pagination import NextTokenPagination
from apps.CORE.deps.sorting import BaseSorting
from apps.CORE.schemas import JSENDOutSchema
from apps.CORE.models import Group, Permission, Role

groups_router = APIRouter(prefix="/auth/groups", tags=["authorization"], dependencies=[Depends(bearer_auth)])
roles_router = APIRouter(prefix="/auth/roles", tags=["authorization"], dependencies=[Depends(bearer_auth)])
permissions_router = APIRouter(prefix="/auth/permissions", tags=["authorization"], dependencies=[Depends(bearer_auth)])


@groups_router.post(path="/", name="create_group", status_code=status.HTTP_201_CREATED)
async def create_group(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    data: GroupCreateSchema = Body(),
) -> JSENDOutSchema[GroupOutSchema]:
    return JSENDOutSchema[GroupOutSchema](
        data=await groups_handler.create_group(request=request, session=session, data=data),
        message="Group object created successfully.",
        code=status.HTTP_201_CREATED,
    )


@groups_router.get(path="/", name="list_groups", response_model=GroupListOutSchema, status_code=status.HTTP_200_OK)
async def list_groups(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    pagination: NextTokenPagination = Depends(NextTokenPagination()),
    sorting: list[UnaryExpression] = Depends(
        BaseSorting(model=Group, schema=GroupOutSchema, available_columns=[Group.created_at, Group.title])
    ),
) -> GroupListOutSchema:
    total, groups = await groups_handler.list_groups(
        session=session, request=request, pagination=pagination, sorting=sorting
    )
    return GroupListOutSchema(
        data=pagination.paginate(
            request=request,
            objects=groups,
            schema=GroupOutSchema,
            total=total,
            endpoint_name="list_groups",
        ),
        message="Paginated list of Group objects.",
    )


@groups_router.get(
    path="/{id}/", name="read_group", response_model=JSENDOutSchema[GroupOutSchema], status_code=status.HTTP_200_OK
)
async def read_group(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    id: uuid.UUID = Path(),
) -> JSENDOutSchema[GroupOutSchema]:
    return JSENDOutSchema[GroupOutSchema](
        data=await groups_handler.read_group(request=request, session=session, id=id), message="Group details."
    )


@groups_router.patch(
    path="/{id}/", name="update_group", response_model=JSENDOutSchema[GroupOutSchema], status_code=status.HTTP_200_OK
)
async def update_group(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    id: uuid.UUID = Path(),
    data: GroupUpdateSchema = Body(),
) -> JSENDOutSchema[GroupOutSchema]:
    return JSENDOutSchema[GroupOutSchema](
        data=await groups_handler.update_group(request=request, session=session, id=id, data=data),
        message="Group details.",
    )


@groups_router.delete(path="/{id}/", name="delete_group", response_model=JSENDOutSchema[typing.Type[None]])
async def delete_group(
    request: Request, id: uuid.UUID = Path(), session: AsyncSession = Depends(get_async_session)
) -> JSENDOutSchema[typing.Type[None]]:
    await groups_handler.delete_group(session=session, request=request, id=id)
    return JSENDOutSchema(data=None, message="Group deleted successfully.")


@roles_router.get(path="/", name="list_roles", response_model=RoleListOutSchema, status_code=status.HTTP_200_OK)
async def list_roles(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    pagination: NextTokenPagination = Depends(NextTokenPagination()),
    sorting: list[UnaryExpression] = Depends(
        BaseSorting(model=Role, schema=RoleOutSchema, available_columns=[Role.created_at, Role.title])
    ),
) -> RoleListOutSchema:
    total, roles = await roles_handler.list_roles(
        session=session, request=request, pagination=pagination, sorting=sorting
    )
    return RoleListOutSchema(
        data=pagination.paginate(
            request=request,
            objects=roles,
            schema=RoleOutSchema,
            total=total,
            endpoint_name="list_roles",
        ),
        message="Paginated list of Role objects.",
    )


@roles_router.get(
    path="/{id}/", name="read_role", response_model=JSENDOutSchema[RoleOutSchema], status_code=status.HTTP_200_OK
)
async def read_role(
    request: Request, session: AsyncSession = Depends(get_async_session), id: uuid.UUID = Path()
) -> JSENDOutSchema[RoleOutSchema]:
    return JSENDOutSchema[RoleOutSchema](
        data=await roles_handler.read_role(request=request, session=session, id=id), message="Role details."
    )


@roles_router.post(
    path="/", name="create_role", response_model=JSENDOutSchema[RoleOutSchema], status_code=status.HTTP_201_CREATED
)
async def create_role(
    request: Request, session: AsyncSession = Depends(get_async_session), data: RoleCreateSchema = Body()
) -> JSENDOutSchema[RoleOutSchema]:
    return JSENDOutSchema[RoleOutSchema](
        data=await roles_handler.create_role(request=request, session=session, data=data),
        message="Role object created successfully.",
        code=status.HTTP_201_CREATED,
    )


@roles_router.delete(
    path="/{id}/", name="delete_role", response_model=JSENDOutSchema[typing.Type[None]], status_code=status.HTTP_200_OK
)
async def delete_role(
    request: Request, id: uuid.UUID = Path(), session: AsyncSession = Depends(get_async_session)
) -> JSENDOutSchema[typing.Type[None]]:
    await roles_handler.delete_role(session=session, request=request, id=id)
    return JSENDOutSchema(data=None, message="Role deleted successfully.")


@permissions_router.get(
    path="/", name="list_permissions", response_model=PermissionListOutSchema, status_code=status.HTTP_200_OK
)
async def list_permissions(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    pagination: NextTokenPagination = Depends(NextTokenPagination()),
    sorting: list[UnaryExpression] = Depends(
        BaseSorting(
            model=Permission,
            schema=PermissionOutSchema,
            available_columns=[Permission.id, Permission.created_at, Permission.object_name],
        )
    ),
) -> PermissionListOutSchema:
    total, permissions = await permissions_handler.list_permissions(
        session=session, request=request, pagination=pagination, sorting=sorting
    )
    return PermissionListOutSchema(
        data=pagination.paginate(
            request=request,
            objects=permissions,
            schema=PermissionOutSchema,
            total=total,
            endpoint_name="list_permissions",
        ),
        message="Paginated list of Permission objects.",
    )


@permissions_router.get(
    path="/{id}/",
    name="read_permission",
    response_model=JSENDOutSchema[PermissionOutSchema],
    status_code=status.HTTP_200_OK,
)
async def read_permission(
    request: Request, session: AsyncSession = Depends(get_async_session), id: uuid.UUID = Path()
) -> JSENDOutSchema[PermissionOutSchema]:
    return JSENDOutSchema[PermissionOutSchema](
        data=await permissions_handler.read_permission(request=request, session=session, id=id),
        message="Permission details.",
    )
