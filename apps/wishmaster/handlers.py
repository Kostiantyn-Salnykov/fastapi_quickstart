import typing

from fastapi import Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.CORE.custom_types import StrOrUUID
from apps.CORE.deps.body.filtration import Filtration
from apps.CORE.deps.body.pagination import Pagination
from apps.CORE.deps.body.projection import Projection
from apps.CORE.deps.body.searching import Searching
from apps.CORE.deps.body.sorting import Sorting
from apps.CORE.exceptions import BackendError
from apps.CORE.helpers import to_db_encoder
from apps.wishmaster.models import WishList
from apps.wishmaster.schemas import (
    WishListCreateSchema,
    WishListResponseSchema,
    WishListToDBCreateSchema,
)
from apps.wishmaster.services import wishlist_service


class WishlistHandler:
    async def create(
        self, *, session: AsyncSession, request: Request, data: WishListCreateSchema
    ) -> WishListResponseSchema:
        data = WishListToDBCreateSchema(**data.model_dump(), owner_id=request.user.id)
        values: dict[str, typing.Any] = to_db_encoder(obj=data)
        wishlist: WishList = await wishlist_service.create(session=session, values=values)
        return WishListResponseSchema.from_model(obj=wishlist)

    async def list(
        self,
        *,
        session: AsyncSession,
        request: Request,
        sorting: Sorting,
        pagination: Pagination,
        filtration: Filtration,
        projection: Projection,
        searching: Searching,
    ) -> tuple[int, list[WishList]]:
        filtration.query.extend([WishList.owner_id == request.user.id])
        return await wishlist_service.list(
            session=session,
            sorting=sorting,
            pagination=pagination,
            filtration=filtration,
            projection=projection,
            searching=searching,
        )

    async def delete(self, *, session: AsyncSession, request: Request, id: StrOrUUID, safe: bool = False) -> None:
        result = await wishlist_service.delete(session=session, id=id)
        if not result.rowcount and not safe:
            raise BackendError(message="WishList not found.", code=status.HTTP_404_NOT_FOUND)
        return None


wishlist_handler = WishlistHandler()
