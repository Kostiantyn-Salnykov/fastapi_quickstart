from core.annotations import StrOrNone
from core.custom_types import StrUUID
from core.schemas.mixins import CreatedUpdatedResponseMixin
from core.schemas.requests import BaseRequestSchema
from core.schemas.responses import BaseResponseSchema, JSENDPaginationResponseSchema, PaginationResponseSchema
from pydantic import Field, field_validator

from src.api.wishmaster.enums import WishComplexities, WishPriorities, WishStatuses
from src.api.wishmaster.tables import Tag


class CategoryResponseSchema(BaseResponseSchema):
    title: str = Field(default=..., max_length=128)
    owner_id: StrUUID = Field(...)


class TagResponseSchema(BaseResponseSchema):
    title: str = Field(default=..., max_length=64)


class WishCreateToDBSchema(BaseRequestSchema):
    title: str = Field(max_length=128)
    wishlist_id: StrUUID = Field(default=..., alias="wishlistId")
    status: WishStatuses = Field(default=WishStatuses.CREATED)
    complexity: WishComplexities = Field(default=WishComplexities.NORMAL)
    priority: WishPriorities = Field(default=WishPriorities.NORMAL)
    category_id: StrUUID | None = Field(default=None, alias="categoryId")
    description: StrOrNone = Field(default=None, max_length=255)


class WishCreateSchema(WishCreateToDBSchema):
    tags: list[str] | None = Field(default_factory=list, max_length=10)


class WishUpdateToDBSchema(WishCreateSchema):
    title: StrOrNone = Field(default=None, max_length=128)
    wishlist_id: StrUUID | None = Field(default=None, alias="wishlistId")
    status: WishStatuses | None = Field(default=WishStatuses.CREATED)
    description: StrOrNone = Field(default=None, max_length=255)


class WishUpdateSchema(WishUpdateToDBSchema):
    tags: list[str] | None = Field(default=None, max_length=10)


class WishResponseSchema(BaseResponseSchema, CreatedUpdatedResponseMixin):
    id: StrUUID
    title: str = Field(max_length=128)
    wishlist_id: StrUUID = Field(default=..., alias="wishlistId")
    status: WishStatuses = Field(default=...)
    complexity: WishComplexities = Field(default=...)
    priority: WishPriorities = Field(default=...)
    category_id: StrUUID | None = Field(default=None, alias="categoryId")
    description: StrOrNone = Field(default=None, max_length=255)

    category: CategoryResponseSchema | None = Field(default=None)
    tags: list[str] = Field(default_factory=list)

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tag(cls, v: list[Tag | str]) -> list[str]:
        tags: list[str] = [tag.title if isinstance(tag, Tag) else tag for tag in v]
        return tags


class WishesOutSchema(JSENDPaginationResponseSchema):
    data: PaginationResponseSchema[WishResponseSchema]


class WishListCreateSchema(BaseRequestSchema):
    title: str = Field(max_length=128)


class WishListToDBCreateSchema(WishListCreateSchema):
    owner_id: StrUUID = Field(...)


class WishListResponseSchema(BaseResponseSchema, CreatedUpdatedResponseMixin):
    id: StrUUID | None = Field(default=None)
    title: StrOrNone = Field(default=None, max_length=128)
    owner_id: StrUUID | None = Field(default=None, alias="ownerId")


class WishListWithWishesOutSchema(WishListResponseSchema):
    wishes: list[WishResponseSchema] | None = Field(default_factory=list)


class WishListsResponseSchema(BaseResponseSchema, JSENDPaginationResponseSchema):
    data: PaginationResponseSchema[WishListWithWishesOutSchema]
