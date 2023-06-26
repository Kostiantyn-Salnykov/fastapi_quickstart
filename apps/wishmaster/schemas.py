import uuid

from pydantic import Field, validator

from apps.CORE.schemas import (
    BaseInSchema,
    BaseOutSchema,
    CreatedUpdatedOutSchema,
    JSENDPaginationOutSchema,
    PaginationOutSchema,
)
from apps.wishmaster.enums import WishComplexities, WishPriorities, WishStatuses
from apps.wishmaster.models import Tag


class CategoryOutSchema(BaseOutSchema):
    title: str = Field(default=..., max_length=128)
    owner_id: uuid.UUID = Field(...)


class TagOutSchema(BaseOutSchema):
    title: str = Field(default=..., max_length=64)


class WishCreateToDBSchema(BaseInSchema):
    title: str = Field(max_length=128, example="Do something.")
    wishlist_id: uuid.UUID = Field(default=..., alias="wishlistId")
    status: WishStatuses = Field(default=WishStatuses.CREATED)
    complexity: WishComplexities = Field(default=WishComplexities.NORMAL)
    priority: WishPriorities = Field(default=WishPriorities.NORMAL)
    category_id: uuid.UUID | None = Field(default=None, alias="categoryId")
    description: str | None = Field(max_length=255)


class WishCreateSchema(WishCreateToDBSchema):
    tags: list[str] | None = Field(default=[], max_items=10)


class WishUpdateToDBSchema(WishCreateSchema):
    title: str | None = Field(default=None, max_length=128)
    wishlist_id: uuid.UUID | None = Field(default=None, alias="wishlistId")
    status: WishStatuses | None = Field(default=WishStatuses.CREATED)
    description: str | None = Field(default=None, max_length=255)


class WishUpdateSchema(WishUpdateToDBSchema):
    tags: list[str] | None = Field(default=None, max_items=10)


class WishOutSchema(BaseOutSchema, CreatedUpdatedOutSchema):
    id: uuid.UUID
    title: str = Field(max_length=128, example="Do something.")
    wishlist_id: uuid.UUID = Field(default=..., alias="wishlistId")
    status: WishStatuses = Field(default=...)
    complexity: WishComplexities = Field(default=...)
    priority: WishPriorities = Field(default=...)
    category_id: uuid.UUID | None = Field(default=None, alias="categoryId")
    description: str | None = Field(default=None, max_length=255)

    category: CategoryOutSchema | None = Field(default=None)
    tags: list[str] = Field(default=[])

    @validator("tags", pre=True)
    def validate_tag(cls, v: list[Tag | str]) -> list[str]:
        tags: list[str] = [getattr(tag, "title") if isinstance(tag, Tag) else tag for tag in v]
        return tags


class WishesOutSchema(JSENDPaginationOutSchema):
    data: PaginationOutSchema[WishOutSchema]


class WishListCreateSchema(BaseInSchema):
    title: str = Field(max_length=128, example="My Wishlist")


class WishListToDBCreateSchema(WishListCreateSchema):
    owner_id: uuid.UUID = Field(...)


class WishListOutSchema(BaseOutSchema, CreatedUpdatedOutSchema):
    id: uuid.UUID
    title: str = Field(max_length=128, example="My Wishlist")
    owner_id: uuid.UUID = Field(alias="ownerId")


class WishListWithWishesOutSchema(WishListOutSchema):
    wishes: list[WishOutSchema] | None = Field(default=[])


class WishListsOutSchema(BaseOutSchema, JSENDPaginationOutSchema):
    data: PaginationOutSchema[WishListWithWishesOutSchema]
