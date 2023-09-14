from typing import Generic

from fastapi import status as http_status
from pydantic import BaseModel, ConfigDict, Field

from apps.CORE.custom_types import ModelType, ObjectsVar, SchemaType, StrOrNone
from apps.CORE.enums import JSENDStatus
from apps.CORE.schemas.requests import BaseRequestSchema


class BaseResponseSchema(BaseRequestSchema):
    """Base schema for schemas that will be used in responses."""

    model_config = ConfigDict(
        validate_assignment=True,
        from_attributes=True,
        strict=False,
        defer_build=True,
    )

    @classmethod
    def from_model(cls, obj: SchemaType) -> ModelType:
        # TableNameMixin.to_dict() logic.
        obj = obj.to_dict()
        # Pydantic from_orm logic.
        model = cls.__new__(cls)
        model = model.model_validate(obj=obj, strict=False, from_attributes=True)
        return model


class JSENDResponse(BaseModel, Generic[SchemaType]):
    """JSEND schema with 'success' status."""

    status: JSENDStatus = Field(default=JSENDStatus.SUCCESS)
    data: SchemaType | None = Field(default=None)
    message: str = Field(default=...)
    code: int = Field(default=http_status.HTTP_200_OK)


class JSENDFailResponse(JSENDResponse[SchemaType]):
    """JSEND schema with 'fail' status (validation errors, client errors)."""

    status: JSENDStatus = Field(default=JSENDStatus.FAIL)
    data: SchemaType = Field(default=None)


class JSENDErrorResponse(JSENDResponse[SchemaType]):
    """JSEND schema with 'error' status (server errors)."""

    status: JSENDStatus = Field(default=JSENDStatus.ERROR)
    data: SchemaType = Field(default=None)


class UnprocessableEntityResponse(BaseResponseSchema):
    """Schema that uses in pydantic validation errors."""

    location: list[str] = Field(example=["body", "field_1"])
    message: str = Field(example="Field required.")
    type: str = Field(example="missing")
    context: StrOrNone = Field(default=None)


class PaginationResponse(BaseModel, Generic[ObjectsVar]):
    """Generic ResponseSchema that uses for pagination."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    objects: list[ObjectsVar]
    offset: int | None = Field(default=None, description="Number of objects to skip.")
    limit: int = Field(default=100, description="Number of objects returned per one page.")
    total_count: int = Field(
        default=..., alias="totalCount", description="Numbed of objects counted inside db for this query."
    )
    next_token: StrOrNone = Field(
        default=None,
        alias="nextToken",
        title="Next Token",
        description="This is the latest `id` of previous result.",
    )
    page: int | None = Field(default=None, title="Page", description="Current page (depends on offset, limit).")
    pages: int | None = Field(
        default=None, title="Pages", description="Total number of pages (depends on limit and total number of records)."
    )


class JSENDPaginationResponse(JSENDResponse[SchemaType]):
    """Cover PaginationOutSchema with JSEND structure."""

    data: PaginationResponse[SchemaType] = Field(default=...)
