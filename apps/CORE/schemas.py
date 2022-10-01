import datetime
import uuid
from typing import Generic, TypeVar

import orjson
import pydantic.json
from fastapi import status as http_status
from pydantic import AnyHttpUrl, BaseModel, Field
from pydantic.generics import GenericModel

from apps.CORE.enums import JSENDStatus
from apps.CORE.types import Timestamp
from apps.CORE.utils import get_timestamp, orjson_dumps

SchemaVar = TypeVar(name="SchemaVar", bound=BaseModel | None)
ObjectsVar = TypeVar(name="ObjectsVar", bound=dict[str, None | str | int | float | dict | list])


class BaseInSchema(BaseModel):
    class Config:
        """Schema configuration."""

        orm_mode = True
        arbitrary_types_allowed = True
        validate_assignment = True
        allow_population_by_field_name = True
        use_enum_values = True


class BaseOutSchema(BaseInSchema):
    class Config(BaseInSchema.Config):
        """Schema configuration."""

        json_encoders = {
            # field type: encoder function
            datetime.datetime: get_timestamp,
            datetime.timedelta: lambda time_delta: pydantic.json.timedelta_isoformat(time_delta),
            uuid.UUID: str,
        }
        json_dumps = orjson_dumps
        json_loads = orjson.loads


class JSENDOutSchema(GenericModel, Generic[SchemaVar]):
    status: JSENDStatus = Field(default=JSENDStatus.SUCCESS)
    data: SchemaVar
    message: str
    code: int = Field(default=http_status.HTTP_200_OK)


class JSENDFailOutSchema(JSENDOutSchema):
    status: JSENDStatus = Field(default=JSENDStatus.FAIL)
    data: str | None


class JSENDErrorOutSchema(JSENDOutSchema):
    status: JSENDStatus = Field(default=JSENDStatus.ERROR)
    data: str | None


class UnprocessableEntityOutSchema(BaseOutSchema):
    location: list[str] = Field(example=["body", "field_1"])
    message: str = Field(example="Field required.")
    type: str = Field(example="value_error.missing")
    context: str | None


class CreatedAtOutSchema(BaseModel):
    created_at: Timestamp = Field(title="Created at", alias="createdAt")


class UpdatedAtOutSchema(BaseModel):
    updated_at: Timestamp = Field(title="Updated at", alias="updatedAt")


class CreatedUpdatedOutSchema(CreatedAtOutSchema, UpdatedAtOutSchema):
    ...


class PaginationOutSchema(GenericModel, Generic[ObjectsVar]):
    objects: list[ObjectsVar]
    offset: int = Field(default=0)
    limit: int = Field(default=100)
    next_uri: AnyHttpUrl | None = Field(default=None, title="Next URI")
    previous_uri: AnyHttpUrl | None = Field(default=None, title="Previous URI")

    class Config(BaseOutSchema.Config):
        ...


class JSENDPaginationOutSchema(JSENDOutSchema):
    data: PaginationOutSchema
