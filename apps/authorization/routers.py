import uuid

from fastapi import APIRouter, Body, Depends, Path, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import UnaryExpression

from apps.authorization.dependencies import bearer_auth
from apps.authorization.handlers import groups_handler, permissions_handler, roles_handler
from apps.authorization.models import Group, Permission, Role
from apps.authorization.schemas import (
    GroupCreateSchema,
    GroupListOutSchema,
    GroupOutSchema,
    PermissionListOutSchema,
    PermissionOutSchema,
    RoleCreateSchema,
    RoleListOutSchema,
    RoleOutSchema,
)
from apps.CORE.dependencies import BasePagination, BaseSorting, get_async_session
from apps.CORE.schemas import JSENDOutSchema

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
    )


@groups_router.get(path="/", name="list_groups", response_model=GroupListOutSchema)
async def list_groups(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    pagination: BasePagination = Depends(BasePagination()),
    sorting: list[UnaryExpression] = Depends(
        BaseSorting(model=Group, schema=GroupOutSchema, available_columns=[Group.created_at, Group.name])
    ),
) -> GroupListOutSchema:
    total, groups = await groups_handler.list_groups(
        session=session, request=request, pagination=pagination, sorting=sorting
    )
    return GroupListOutSchema(
        data=BasePagination.paginate(
            pagination=pagination,
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


@roles_router.get(path="/", name="list_roles", response_model=RoleListOutSchema)
async def list_roles(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    pagination: BasePagination = Depends(BasePagination()),
    sorting: list[UnaryExpression] = Depends(
        BaseSorting(model=Role, schema=RoleOutSchema, available_columns=[Role.created_at, Role.name])
    ),
) -> RoleListOutSchema:
    total, roles = await roles_handler.list_roles(
        session=session, request=request, pagination=pagination, sorting=sorting
    )
    return RoleListOutSchema(
        data=BasePagination.paginate(
            pagination=pagination,
            request=request,
            objects=roles,
            schema=RoleOutSchema,
            total=total,
            endpoint_name="list_roles",
        ),
        message="Paginated list of Role objects.",
    )


@roles_router.get(path="/{id}/", name="read_role", response_model=JSENDOutSchema[RoleOutSchema])
async def read_role(
    request: Request, session: AsyncSession = Depends(get_async_session), id: uuid.UUID = Path()
) -> JSENDOutSchema[RoleOutSchema]:
    return JSENDOutSchema[RoleOutSchema](
        data=await roles_handler.read_role(request=request, session=session, id=id), message="Role details."
    )


@roles_router.post(path="/", name="create_role", response_model=JSENDOutSchema[RoleOutSchema])
async def create_role(
    request: Request, session: AsyncSession = Depends(get_async_session), data: RoleCreateSchema = Body()
) -> JSENDOutSchema[RoleOutSchema]:
    return JSENDOutSchema[RoleOutSchema](
        data=await roles_handler.create_role(request=request, session=session, data=data),
        message="Role object created successfully.",
    )


@permissions_router.get(path="/", name="list_permissions", response_model=PermissionListOutSchema)
async def list_permissions(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    pagination: BasePagination = Depends(BasePagination()),
    sorting: list[UnaryExpression] = Depends(
        BaseSorting(
            model=Permission,
            schema=PermissionOutSchema,
            available_columns=[Permission.created_at, Permission.object_name],
        )
    ),
) -> PermissionListOutSchema:
    total, permissions = await permissions_handler.list_permissions(
        session=session, request=request, pagination=pagination, sorting=sorting
    )
    return PermissionListOutSchema(
        data=BasePagination.paginate(
            pagination=pagination,
            request=request,
            objects=permissions,
            schema=PermissionOutSchema,
            total=total,
            endpoint_name="list_permissions",
        ),
        message="Paginated list of Permission objects.",
    )


@permissions_router.get(path="/{id}/", name="read_permission", response_model=JSENDOutSchema[PermissionOutSchema])
async def read_permission(
    request: Request, session: AsyncSession = Depends(get_async_session), id: uuid.UUID = Path()
) -> JSENDOutSchema[PermissionOutSchema]:
    return JSENDOutSchema[PermissionOutSchema](
        data=await permissions_handler.read_permission(request=request, session=session, id=id),
        message="Permission details.",
    )
