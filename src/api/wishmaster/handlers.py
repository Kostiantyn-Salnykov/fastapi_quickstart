import typing

from core.annotations import StrOrUUID
from core.deps.body.filtration import Filtration
from core.deps.body.pagination import Pagination
from core.deps.body.projection import Projection
from core.deps.body.searching import Searching
from core.deps.body.sorting import Sorting
from core.exceptions import BackendError
from core.helpers import to_db_encoder
from fastapi import Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.wishmaster.schemas import WishListCreateSchema, WishListResponseSchema, WishListToDBCreateSchema
from src.api.wishmaster.services import wishlist_service
from src.api.wishmaster.tables import WishList


class WishlistHandler:
    async def create(
        self,
        *,
        session: AsyncSession,
        request: Request,
        data: WishListCreateSchema,
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
        filtration = [WishList.id == id, WishList.owner_id == request.user.id]
        result = await wishlist_service.delete(session=session, filtration=filtration)
        if not result.rowcount and not safe:
            raise BackendError(message="Wishlist not found.", code=status.HTTP_404_NOT_FOUND)


wishlist_handler = WishlistHandler()
