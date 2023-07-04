import datetime
import typing
import uuid

from fastapi import APIRouter, Body, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import BinaryExpression, UnaryExpression

from apps.authorization.dependencies import IsAuthenticated, bearer_auth
from apps.CORE.deps import get_async_session
from apps.CORE.deps.filters import BaseFilters, F
from apps.CORE.deps.pagination import NextTokenPagination
from apps.CORE.deps.sorting import BaseSorting
from apps.CORE.enums import FOps
from apps.CORE.responses import Responses
from apps.CORE.schemas.responses import JSENDResponse
from apps.wishmaster.enums import WishComplexities, WishPriorities
from apps.wishmaster.handlers import wish_handler, wishlist_handler
from apps.wishmaster.models import Wish, WishList
from apps.wishmaster.schemas import (
    WishCreateSchema,
    WishesOutSchema,
    WishListCreateSchema,
    WishListResponseSchema,
    WishListsResponseSchema,
    WishListWithWishesOutSchema,
    WishResponseSchema,
    WishUpdateSchema,
)

wishlist_router = APIRouter(
    prefix="/wishlists",
    tags=["wishlists"],
    dependencies=[Depends(bearer_auth), Depends(IsAuthenticated())],
    responses=Responses.AUTH,
)
wish_router = APIRouter(
    prefix="/wishes", tags=["wishes"], dependencies=[Depends(bearer_auth), Depends(IsAuthenticated())]
)


@wishlist_router.post(path="/", name="create_wishlist", response_model=JSENDResponse[WishListResponseSchema])
async def create_wishlist(
    request: Request, data: WishListCreateSchema, session: AsyncSession = Depends(get_async_session)
) -> JSENDResponse[WishListResponseSchema]:
    return JSENDResponse[WishListResponseSchema](
        data=await wishlist_handler.create(session=session, request=request, data=data),
        message="Created WishList details.",
    )


@wishlist_router.get(
    path="/",
    name="list_wishlists",
    response_model=WishListsResponseSchema,
)
async def list_wishlists(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    pagination: NextTokenPagination = Depends(NextTokenPagination()),
    sorting: list[UnaryExpression] = Depends(
        BaseSorting(
            model=WishList,
            schema=WishListResponseSchema,
            available_columns=[WishList.id, WishList.created_at, WishList.title],
        )
    ),
    filters: list[BinaryExpression] = Depends(
        BaseFilters(
            model=WishList,
            schema=WishListResponseSchema,
            filters=[
                F(
                    query_field_name="createdAt",
                    possible_operations=[FOps.G, FOps.LE, FOps.EQ, FOps.NE],
                    value_type=datetime.datetime,
                ),
                F(
                    query_field_name="title",
                    possible_operations=[
                        FOps.EQ,
                        FOps.NE,
                        FOps.IN,
                        FOps.NOT_IN,
                        FOps.LIKE,
                        FOps.ILIKE,
                        FOps.STARTSWITH,
                        FOps.ENDSWITH,
                    ],
                    value_type=list[str] | str,
                ),
            ],
        )
    ),
) -> WishListsResponseSchema:
    total, wishlists = await wishlist_handler.list(
        session=session, request=request, pagination=pagination, sorting=sorting, filters=filters
    )
    return WishListsResponseSchema(
        data=pagination.paginate(
            request=request,
            objects=wishlists,
            schema=WishListWithWishesOutSchema,
            total=total,
            endpoint_name="list_wishlists",
        ),
        message="Paginated list of WishList objects.",
    )


@wishlist_router.delete(path="/{id}/", name="delete_wishlist", response_model=JSENDResponse[type[None]])
async def delete_wishlist(
    request: Request, id: uuid.UUID = Path(), session: AsyncSession = Depends(get_async_session)
) -> JSENDResponse[type[None]]:
    await wishlist_handler.delete(session=session, request=request, id=id)
    return JSENDResponse(data=None, message="WishList deleted successfully.")


@wish_router.post(path="/", response_model=JSENDResponse[WishResponseSchema])
async def create_wish(
    request: Request,
    data: WishCreateSchema = Body(
        examples={
            "minimal": {
                "summary": "A minimal example.",
                "description": "Minimum required fields.",
                "value": {"title": "Wish title!", "wishlistId": "69d1c962-a512-4ac5-a87b-b593452265a8"},
            },
            "normal": {
                "summary": "A normal example.",
                "description": "All possible fields example.",
                "value": {
                    "title": "Wish title!",
                    "wishlistId": "69d1c962-a512-4ac5-a87b-b593452265a8",
                    "status": "CREATED",
                    "complexity": WishComplexities.NORMAL,
                    "priority": WishPriorities.NORMAL,
                    "categoryId": "69d1c962-a512-4ac5-a87b-b593452265a0",
                    "description": "Wish description!",
                },
            },
        },
    ),
    session: AsyncSession = Depends(get_async_session),
) -> JSENDResponse[WishResponseSchema]:
    return JSENDResponse[WishResponseSchema](
        data=await wish_handler.create(session=session, request=request, data=data),
        message="Created Wish details.",
    )


@wish_router.get(path="/", name="list_wishes", response_model=WishesOutSchema)
async def list_wishes(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    pagination: NextTokenPagination = Depends(NextTokenPagination()),
    sorting: list[UnaryExpression] = Depends(
        BaseSorting(
            model=Wish,
            schema=WishResponseSchema,
            available_columns=[Wish.id, Wish.created_at, Wish.title, Wish.priority, Wish.complexity],
        )
    ),
    filters: list[BinaryExpression] = Depends(
        BaseFilters(
            model=Wish,
            schema=WishResponseSchema,
            filters=[
                F(
                    query_field_name="createdAt",
                    possible_operations=[FOps.G, FOps.LE, FOps.EQ, FOps.NE],
                    value_type=datetime.datetime,
                ),
                F(
                    query_field_name="title",
                    possible_operations=[FOps.EQ, FOps.NE, FOps.LIKE, FOps.ILIKE, FOps.STARTSWITH, FOps.ENDSWITH],
                    value_type=str,
                ),
                F(
                    query_field_name="description",
                    possible_operations=[
                        FOps.EQ,
                        FOps.NE,
                        FOps.LIKE,
                        FOps.ILIKE,
                        FOps.STARTSWITH,
                        FOps.ENDSWITH,
                        FOps.IN,
                        FOps.NOT_IN,
                        FOps.NOT_NULL,
                        FOps.ISNULL,
                    ],
                    value_type=list[str] | str | None,
                ),
                F(
                    query_field_name="status",
                    possible_operations=[FOps.EQ, FOps.NE, FOps.IN, FOps.NOT_IN],
                    value_type=list[str] | str,
                ),
            ],
        )
    ),
) -> dict[str, typing.Any]:
    total, wishes = await wish_handler.list(
        session=session, request=request, pagination=pagination, sorting=sorting, filters=filters
    )
    return {
        "data": pagination.paginate(
            request=request,
            objects=wishes,
            schema=WishResponseSchema,
            total=total,
            endpoint_name="list_wishes",
        ),
        "message": "Paginated list of Wish objects.",
    }


@wish_router.delete(path="/{id}/", name="delete_wish", response_model=JSENDResponse)
async def delete_wish(
    request: Request,
    id: uuid.UUID = Path(),
    session: AsyncSession = Depends(get_async_session),
) -> JSENDResponse[type[None]]:
    await wish_handler.delete(session=session, request=request, id=id)
    return JSENDResponse(data=None, message="Wish deleted successfully.")


@wish_router.get(path="/{id}/", name="read_wish", response_model=JSENDResponse[WishResponseSchema])
async def read_wish(
    request: Request, id: uuid.UUID = Path(), session: AsyncSession = Depends(get_async_session)
) -> JSENDResponse[WishResponseSchema]:
    return JSENDResponse[WishResponseSchema](
        data=await wish_handler.read(session=session, request=request, id=id),
        message="Wish details.",
    )


@wish_router.patch(path="/{id}/", name="update_wish", response_model=JSENDResponse[WishResponseSchema])
async def update_wish(
    request: Request, data: WishUpdateSchema, id: uuid.UUID = Path(), session: AsyncSession = Depends(get_async_session)
) -> JSENDResponse[WishResponseSchema]:
    return JSENDResponse[WishResponseSchema](
        data=await wish_handler.update(session=session, request=request, id=id, data=data),
        message="Updated Wish details.",
    )
