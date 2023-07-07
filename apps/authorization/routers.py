import uuid

from fastapi import APIRouter, Body, Depends, Path, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import BinaryExpression, UnaryExpression

from apps.authorization.dependencies import bearer_auth
from apps.authorization.handlers import groups_handler, permissions_handler, roles_handler
from apps.authorization.schemas.requests import GroupCreateRequest, GroupUpdateRequest, RoleCreateRequest
from apps.authorization.schemas.responses import (
    GroupListResponse,
    GroupResponse,
    PermissionListResponse,
    PermissionResponse,
    RoleListResponse,
    RoleResponse,
)
from apps.CORE.deps import get_async_session
from apps.CORE.deps.filters import BaseFilters, F
from apps.CORE.deps.pagination import NextTokenPagination
from apps.CORE.deps.sorting import BaseSorting
from apps.CORE.enums import FOps
from apps.CORE.models import Group, Permission, Role
from apps.CORE.schemas.responses import JSENDResponse

groups_router = APIRouter(prefix="/auth/groups", tags=["authorization"], dependencies=[Depends(bearer_auth)])
roles_router = APIRouter(prefix="/auth/roles", tags=["authorization"], dependencies=[Depends(bearer_auth)])
permissions_router = APIRouter(prefix="/auth/permissions", tags=["authorization"], dependencies=[Depends(bearer_auth)])


@groups_router.post(path="/", name="create_group", status_code=status.HTTP_201_CREATED)
async def create_group(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    data: GroupCreateRequest = Body(),
) -> JSENDResponse[GroupResponse]:
    return JSENDResponse[GroupResponse](
        data=await groups_handler.create_group(request=request, session=session, data=data),
        message="Group object created successfully.",
        code=status.HTTP_201_CREATED,
    )


@groups_router.get(path="/", name="list_groups", response_model=GroupListResponse, status_code=status.HTTP_200_OK)
async def list_groups(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    pagination: NextTokenPagination = Depends(NextTokenPagination()),
    sorting: list[UnaryExpression] = Depends(
        BaseSorting(model=Group, schema=GroupResponse, available_columns=[Group.created_at, Group.title])
    ),
    filters: list[BinaryExpression] = Depends(
        BaseFilters(
            model=Permission,
            schema=PermissionResponse,
            filters=[
                F(
                    query_field_name="title",
                    possible_operations=[FOps.EQ, FOps.IN, FOps.NE, FOps.NOT_IN, FOps.STARTSWITH, FOps.ENDSWITH],
                    value_type=list[str] | str,
                )
            ],
        )
    ),
) -> GroupListResponse:
    total, groups = await groups_handler.list_groups(
        session=session, request=request, pagination=pagination, sorting=sorting, filters=filters
    )
    return GroupListResponse(
        data=pagination.paginate(
            request=request,
            objects=groups,
            schema=GroupResponse,
            total=total,
            endpoint_name="list_groups",
        ),
        message="Paginated list of Group objects.",
    )


@groups_router.get(
    path="/{id}/",
    name="read_group",
    response_model=JSENDResponse[GroupResponse],
    status_code=status.HTTP_200_OK,
)
async def read_group(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    id: uuid.UUID = Path(),
) -> JSENDResponse[GroupResponse]:
    return JSENDResponse[GroupResponse](
        data=await groups_handler.read_group(request=request, session=session, id=id), message="Group details."
    )


@groups_router.patch(
    path="/{id}/",
    name="update_group",
    response_model=JSENDResponse[GroupResponse],
    status_code=status.HTTP_200_OK,
)
async def update_group(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    id: uuid.UUID = Path(),
    data: GroupUpdateRequest = Body(),
) -> JSENDResponse[GroupResponse]:
    return JSENDResponse[GroupResponse](
        data=await groups_handler.update_group(request=request, session=session, id=id, data=data),
        message="Group details.",
    )


@groups_router.delete(path="/{id}/", name="delete_group", response_model=JSENDResponse[type[None]])
async def delete_group(
    request: Request, id: uuid.UUID = Path(), session: AsyncSession = Depends(get_async_session)
) -> JSENDResponse[type[None]]:
    await groups_handler.delete_group(session=session, request=request, id=id)
    return JSENDResponse(data=None, message="Group deleted successfully.")


@roles_router.get(path="/", name="list_roles", response_model=RoleListResponse, status_code=status.HTTP_200_OK)
async def list_roles(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    pagination: NextTokenPagination = Depends(NextTokenPagination()),
    sorting: list[UnaryExpression] = Depends(
        BaseSorting(model=Role, schema=RoleResponse, available_columns=[Role.created_at, Role.title])
    ),
    filters: list[BinaryExpression] = Depends(
        BaseFilters(
            model=Permission,
            schema=PermissionResponse,
            filters=[
                F(
                    query_field_name="title",
                    possible_operations=[FOps.EQ, FOps.IN, FOps.NE, FOps.NOT_IN, FOps.STARTSWITH, FOps.ENDSWITH],
                    value_type=list[str] | str,
                )
            ],
        )
    ),
) -> RoleListResponse:
    total, roles = await roles_handler.list_roles(
        session=session, request=request, pagination=pagination, sorting=sorting, filters=filters
    )
    return RoleListResponse(
        data=pagination.paginate(
            request=request,
            objects=roles,
            schema=RoleResponse,
            total=total,
            endpoint_name="list_roles",
        ),
        message="Paginated list of Role objects.",
    )


@roles_router.get(
    path="/{id}/", name="read_role", response_model=JSENDResponse[RoleResponse], status_code=status.HTTP_200_OK
)
async def read_role(
    request: Request, session: AsyncSession = Depends(get_async_session), id: uuid.UUID = Path()
) -> JSENDResponse[RoleResponse]:
    return JSENDResponse[RoleResponse](
        data=await roles_handler.read_role(request=request, session=session, id=id), message="Role details."
    )


@roles_router.post(
    path="/", name="create_role", response_model=JSENDResponse[RoleResponse], status_code=status.HTTP_201_CREATED
)
async def create_role(
    request: Request, session: AsyncSession = Depends(get_async_session), data: RoleCreateRequest = Body()
) -> JSENDResponse[RoleResponse]:
    return JSENDResponse[RoleResponse](
        data=await roles_handler.create_role(request=request, session=session, data=data),
        message="Role object created successfully.",
        code=status.HTTP_201_CREATED,
    )


@roles_router.delete(
    path="/{id}/",
    name="delete_role",
    response_model=JSENDResponse[type[None]],
    status_code=status.HTTP_200_OK,
)
async def delete_role(
    request: Request, id: uuid.UUID = Path(), session: AsyncSession = Depends(get_async_session)
) -> JSENDResponse[type[None]]:
    await roles_handler.delete_role(session=session, request=request, id=id)
    return JSENDResponse(data=None, message="Role deleted successfully.")


@permissions_router.get(
    path="/",
    name="list_permissions",
    response_model=PermissionListResponse,
    status_code=status.HTTP_200_OK,
    openapi_extra={"examples": [{"summary": "KEK", "description": "hz", "value": '{"f": }'}]},
)
async def list_permissions(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    pagination: NextTokenPagination = Depends(NextTokenPagination()),
    sorting: list[UnaryExpression] = Depends(
        BaseSorting(
            model=Permission,
            schema=PermissionResponse,
            available_columns=[Permission.id, Permission.created_at, Permission.object_name, Permission.action],
        )
    ),
    filters: list[BinaryExpression] = Depends(
        BaseFilters(
            model=Permission,
            schema=PermissionResponse,
            filters=[
                F(
                    query_field_name="objectName",
                    possible_operations=[FOps.EQ, FOps.IN, FOps.NE, FOps.NOT_IN, FOps.STARTSWITH, FOps.ENDSWITH],
                    value_type=list[str] | str,
                )
            ],
        )
    ),
) -> PermissionListResponse:
    total, permissions = await permissions_handler.list_permissions(
        session=session, request=request, pagination=pagination, sorting=sorting, filters=filters
    )
    return PermissionListResponse(
        data=pagination.paginate(
            request=request,
            objects=permissions,
            schema=PermissionResponse,
            total=total,
            endpoint_name="list_permissions",
        ),
        message="Paginated list of Permission objects.",
    )


@permissions_router.get(
    path="/{id}/",
    name="read_permission",
    response_model=JSENDResponse[PermissionResponse],
    status_code=status.HTTP_200_OK,
)
async def read_permission(
    request: Request, session: AsyncSession = Depends(get_async_session), id: uuid.UUID = Path()
) -> JSENDResponse[PermissionResponse]:
    return JSENDResponse[PermissionResponse](
        data=await permissions_handler.read_permission(request=request, session=session, id=id),
        message="Permission details.",
    )
