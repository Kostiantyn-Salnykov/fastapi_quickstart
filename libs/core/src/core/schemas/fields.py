from typing import Annotated

from pydantic import AwareDatetime, Field, TypeAdapter


class Fields:
    password = TypeAdapter(Annotated[str, Field(default=..., min_length=8, max_length=255)])
    first_name = TypeAdapter(Annotated[str, Field(title="First name", max_length=128, alias="firstName")])
    last_name = TypeAdapter(Annotated[str, Field(title="Last name", max_length=128, alias="lastName")])
    created_at = TypeAdapter(Annotated[AwareDatetime, Field(title="Created at", alias="createdAt")])
    updated_at = TypeAdapter(Annotated[AwareDatetime, Field(title="Updated at", alias="updatedAt")])
