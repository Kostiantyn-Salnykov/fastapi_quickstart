import typing
import uuid

from fastapi import APIRouter, Depends, Path, Request
from pydantic import AwareDatetime
from sqlalchemy.ext.asyncio import AsyncSession

from apps.authorization.dependencies import IsAuthenticated, IsAuthorized, bearer_auth
from apps.CORE.deps import get_async_session
from apps.CORE.deps.body.filtration import F, Filtration
from apps.CORE.deps.body.pagination import Pagination
from apps.CORE.deps.body.projection import Projection
from apps.CORE.deps.body.searching import Searching
from apps.CORE.deps.body.sorting import Sorting
from apps.CORE.enums import FOps
from apps.CORE.responses import Responses
from apps.CORE.schemas.responses import JSENDResponse
from apps.wishmaster.handlers import wishlist_handler
from apps.wishmaster.models import WishList
from apps.wishmaster.schemas import (
    WishListCreateSchema,
    WishListResponseSchema,
    WishListsResponseSchema,
    WishListWithWishesOutSchema,
)

wishlist_router = APIRouter(
    prefix="/wishlists",
    tags=["wishlists"],
    dependencies=[Depends(bearer_auth), Depends(IsAuthenticated())],
    responses=Responses.AUTH,
)


@wishlist_router.post(path="/", name="create_wishlist", response_model=JSENDResponse[WishListResponseSchema])
async def create_wishlist(
    request: Request, data: WishListCreateSchema, session: AsyncSession = Depends(get_async_session)
) -> JSENDResponse[WishListResponseSchema]:
    return JSENDResponse[WishListResponseSchema](
        data=await wishlist_handler.create(session=session, request=request, data=data),
        message="Created WishList details.",
    )


@wishlist_router.post(
    path="/list/",
    name="list_wishlists",
    response_model=WishListsResponseSchema,
    response_model_exclude_unset=True,
)
async def list_wishlists(
    request: Request,
    authorization: typing.Annotated[None, Depends(IsAuthorized())],
    sorting: typing.Annotated[
        Sorting,
        Depends(
            Sorting(
                model=WishList,
                schema=WishListWithWishesOutSchema,
                available_columns=[WishList.id, WishList.title, WishList.created_at, WishList.updated_at],
            )
        ),
    ],
    projection: typing.Annotated[Projection, Depends(Projection(model=WishList, schema=WishListWithWishesOutSchema))],
    pagination: typing.Annotated[Pagination, Depends(Pagination(model=WishList, schema=WishListWithWishesOutSchema))],
    filtration: typing.Annotated[
        Filtration,
        Depends(
            Filtration(
                model=WishList,
                schema=WishListWithWishesOutSchema,
                filters=[
                    F(
                        query_field_name="createdAt",
                        possible_operations=[FOps.GE, FOps.LE, FOps.L, FOps.G],
                        value_type=AwareDatetime,
                    ),
                    F(
                        query_field_name="title",
                        possible_operations=[FOps.EQ, FOps.STARTSWITH, FOps.IN],
                        value_type=list[str] | str,
                    ),
                ],
            ),
        ),
    ],
    searching: typing.Annotated[
        Searching,
        Depends(Searching(model=WishList, schema=WishListWithWishesOutSchema, available_columns=[WishList.title])),
    ],
    session: AsyncSession = Depends(get_async_session),
) -> WishListsResponseSchema:
    total, wishlists = await wishlist_handler.list(
        session=session,
        request=request,
        sorting=sorting,
        pagination=pagination,
        filtration=filtration,
        projection=projection,
        searching=searching,
    )
    return WishListsResponseSchema(
        data=pagination.paginate(objects=wishlists, total=total),
        message="Paginated list of WishList objects.",
    )


@wishlist_router.delete(path="/{id}/", name="delete_wishlist", response_model=JSENDResponse)
async def delete_wishlist(
    request: Request, id: uuid.UUID = Path(), session: AsyncSession = Depends(get_async_session)
) -> JSENDResponse:
    await wishlist_handler.delete(session=session, request=request, id=id)
    return JSENDResponse(data=None, message="WishList deleted successfully.")
