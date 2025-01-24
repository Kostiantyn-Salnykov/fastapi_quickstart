from core.repositories import BaseCoreRepository

from src.api.wishmaster.tables import Category, Tag, WishList


class WishListCRUD(BaseCoreRepository): ...


class TagCRUD(BaseCoreRepository): ...


class CategoryCRUD(BaseCoreRepository): ...


wishlist_service = WishListCRUD(model=WishList)
tag_service = TagCRUD(model=Tag)
category_service = CategoryCRUD(model=Category)
