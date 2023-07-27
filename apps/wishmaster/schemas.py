from pydantic import Field, field_validator

from apps.CORE.schemas.mixins import CreatedUpdatedResponseMixin
from apps.CORE.schemas.requests import BaseRequestSchema
from apps.CORE.schemas.responses import BaseResponseSchema, JSENDPaginationResponse, PaginationResponse
from apps.CORE.types import StrUUID
from apps.wishmaster.enums import WishComplexities, WishPriorities, WishStatuses
from apps.wishmaster.models import Tag


class CategoryResponseSchema(BaseResponseSchema):
    title: str = Field(default=..., max_length=128)
    owner_id: StrUUID = Field(...)


class TagResponseSchema(BaseResponseSchema):
    title: str = Field(default=..., max_length=64)


class WishCreateToDBSchema(BaseRequestSchema):
    title: str = Field(max_length=128, example="Do something.")
    wishlist_id: StrUUID = Field(default=..., alias="wishlistId")
    status: WishStatuses = Field(default=WishStatuses.CREATED)
    complexity: WishComplexities = Field(default=WishComplexities.NORMAL)
    priority: WishPriorities = Field(default=WishPriorities.NORMAL)
    category_id: StrUUID | None = Field(default=None, alias="categoryId")
    description: str | None = Field(default=None, max_length=255)


class WishCreateSchema(WishCreateToDBSchema):
    tags: list[str] | None = Field(default_factory=list, max_length=10)


class WishUpdateToDBSchema(WishCreateSchema):
    title: str | None = Field(default=None, max_length=128)
    wishlist_id: StrUUID | None = Field(default=None, alias="wishlistId")
    status: WishStatuses | None = Field(default=WishStatuses.CREATED)
    description: str | None = Field(default=None, max_length=255)


class WishUpdateSchema(WishUpdateToDBSchema):
    tags: list[str] | None = Field(default=None, max_length=10)


class WishResponseSchema(BaseResponseSchema, CreatedUpdatedResponseMixin):
    id: StrUUID
    title: str = Field(max_length=128, example="Do something.")
    wishlist_id: StrUUID = Field(default=..., alias="wishlistId")
    status: WishStatuses = Field(default=...)
    complexity: WishComplexities = Field(default=...)
    priority: WishPriorities = Field(default=...)
    category_id: StrUUID | None = Field(default=None, alias="categoryId")
    description: str | None = Field(default=None, max_length=255)

    category: CategoryResponseSchema | None = Field(default=None)
    tags: list[str] = Field(default_factory=list)

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tag(cls, v: list[Tag | str]) -> list[str]:
        tags: list[str] = [tag.title if isinstance(tag, Tag) else tag for tag in v]
        return tags


class WishesOutSchema(JSENDPaginationResponse):
    data: PaginationResponse[WishResponseSchema]


class WishListCreateSchema(BaseRequestSchema):
    title: str = Field(max_length=128, example="My Wishlist")


class WishListToDBCreateSchema(WishListCreateSchema):
    owner_id: StrUUID = Field(...)


class WishListResponseSchema(BaseResponseSchema, CreatedUpdatedResponseMixin):
    id: StrUUID
    title: str = Field(max_length=128, example="My Wishlist")
    owner_id: StrUUID = Field(alias="ownerId")


class WishListWithWishesOutSchema(WishListResponseSchema):
    wishes: list[WishResponseSchema] | None = Field(default_factory=list)


class WishListsResponseSchema(BaseResponseSchema, JSENDPaginationResponse):
    data: PaginationResponse[WishListWithWishesOutSchema]
