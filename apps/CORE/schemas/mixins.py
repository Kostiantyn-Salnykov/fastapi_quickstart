from pydantic import BaseModel, Field

from apps.CORE.types import Timestamp


class CreatedAtResponseMixin(BaseModel):
    """Schema with `createdAt` Timestamp field."""

    created_at: Timestamp = Field(title="Created at", alias="createdAt")


class UpdatedAtResponseMixin(BaseModel):
    """Schema with `updatedAt` Timestamp field."""

    updated_at: Timestamp = Field(title="Updated at", alias="updatedAt")


class CreatedUpdatedResponseMixin(CreatedAtResponseMixin, UpdatedAtResponseMixin):
    """Schema with `createdAt` and `updatedAt` Timestamp fields."""

    ...
