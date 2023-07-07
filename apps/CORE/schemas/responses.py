import datetime
import uuid
from typing import Generic

import orjson
import pydantic.json
from fastapi import status as http_status
from pydantic import Field, validate_model
from pydantic.generics import GenericModel
from pydantic.main import object_setattr

from apps.CORE.enums import JSENDStatus
from apps.CORE.helpers import get_timestamp, orjson_dumps
from apps.CORE.schemas.requests import BaseRequestSchema
from apps.CORE.types import ModelType, ObjectsVar, SchemaType, StrOrNone, StrUUID


class BaseResponseSchema(BaseRequestSchema):
    """Base schema for schemas that will be used in responses."""

    class Config(BaseRequestSchema.Config):
        """Schema configuration."""

        json_encoders = {
            # field type: encoder function
            datetime.datetime: get_timestamp,
            datetime.timedelta: lambda time_delta: pydantic.json.timedelta_isoformat(time_delta),
            uuid.UUID: str,
        }
        json_dumps = orjson_dumps
        json_loads = orjson.loads

    @classmethod
    def from_orm(cls, obj: SchemaType) -> ModelType:
        # TableNameMixin.to_dict() logic.
        obj = obj.to_dict()
        # Pydantic from_orm logic.
        model = cls.__new__(cls)
        values, fields_set, validation_error = validate_model(cls, obj)
        if validation_error:
            raise validation_error
        object_setattr(model, "__dict__", values)
        object_setattr(model, "__fields_set__", fields_set)
        model._init_private_attributes()
        return model


class JSENDResponse(GenericModel, Generic[SchemaType]):
    """JSEND schema with 'success' status."""

    status: JSENDStatus = Field(default=JSENDStatus.SUCCESS)
    data: SchemaType | None = Field(default=None)
    message: str = Field(default=...)
    code: int = Field(default=http_status.HTTP_200_OK)


class JSENDFailResponse(JSENDResponse):
    """JSEND schema with 'fail' status (validation errors, client errors)."""

    status: JSENDStatus = Field(default=JSENDStatus.FAIL)
    data: StrOrNone = Field(default=None)


class JSENDErrorResponse(JSENDResponse):
    """JSEND schema with 'error' status (server errors)."""

    status: JSENDStatus = Field(default=JSENDStatus.ERROR)
    data: StrOrNone = Field(default=None)


class UnprocessableEntityResponse(BaseResponseSchema):
    """Schema that uses in pydantic validation errors."""

    location: list[str] = Field(example=["body", "field_1"])
    message: str = Field(example="Field required.")
    type: str = Field(example="value_error.missing")
    context: StrOrNone = Field(default=None)


class PaginationResponse(GenericModel, Generic[ObjectsVar]):
    """Generic ResponseSchema that uses for pagination."""

    objects: list[ObjectsVar]
    offset: int | None = Field(default=None, description="Number of objects to skip.")
    limit: int = Field(default=100, description="Number of objects returned per one page.")
    total_count: int = Field(
        default=..., alias="totalCount", description="Numbed of objects counted inside db for this query."
    )
    next_token: StrUUID | None = Field(
        default=None,
        alias="nextToken",
        title="Next Token",
        description="This is the latest `id` of previous result.",
    )
    page: int | None = Field(default=None, title="Page", description="Current page (depends on offset, limit).")
    pages: int = Field(
        default=..., title="Pages", description="Total number of pages (depends on limit and total number of records)."
    )

    class Config(BaseResponseSchema.Config):
        """`allow_population_by_field_name` used only for remove lint error from PyCharm.

        (by default it applies from BaseOutSchema.Config inheritance).

        It also can be defined as:
        ```python
        class Config(BaseOutSchema.Config):
            ...
        ```
        """

        allow_population_by_field_name = True


class JSENDPaginationResponse(JSENDResponse):
    """Cover PaginationOutSchema with JSEND structure."""

    data: PaginationResponse = Field(default=...)
