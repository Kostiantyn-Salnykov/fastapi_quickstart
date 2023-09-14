from sqlalchemy import UnaryExpression, func, select
from sqlalchemy.engine import ChunkedIteratorResult
from sqlalchemy.ext.asyncio import AsyncSession

from apps.CORE.deps.body.filtration import Filtration
from apps.CORE.deps.body.pagination import Pagination
from apps.CORE.deps.body.projection import Projection
from apps.CORE.deps.body.sorting import Sorting
from apps.CORE.repositories import BaseCoreRepository
from apps.wishmaster.models import Category, Tag, WishList


class WishListCRUD(BaseCoreRepository):
    ...


class TagCRUD(BaseCoreRepository):
    ...


class CategoryCRUD(BaseCoreRepository):
    ...


wishlist_service = WishListCRUD(model=WishList)
tag_service = TagCRUD(model=Tag)
category_service = CategoryCRUD(model=Category)
