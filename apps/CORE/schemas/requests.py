from pydantic import BaseModel, ConfigDict


class BaseRequestSchema(BaseModel):
    """Base schema for schemas that will be used in request validations."""

    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )
