from pydantic import AwareDatetime, BaseModel, Field


class CreatedAtResponseMixin(BaseModel):
    """Schema with `createdAt` Timestamp field."""

    created_at: AwareDatetime | None = Field(default=None, title="Created at", alias="createdAt")


class UpdatedAtResponseMixin(BaseModel):
    """Schema with `updatedAt` Timestamp field."""

    updated_at: AwareDatetime | None = Field(default=None, title="Updated at", alias="updatedAt")


class CreatedUpdatedResponseMixin(CreatedAtResponseMixin, UpdatedAtResponseMixin):
    """Schema with `createdAt` and `updatedAt` Timestamp fields."""

    ...
