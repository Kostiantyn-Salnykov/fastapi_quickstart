from pydantic import BaseModel


class BaseRequestSchema(BaseModel):
    """Base schema for schemas that will be used in request validations."""

    class Config:
        """Schema configuration."""

        orm_mode = True
        arbitrary_types_allowed = True
        validate_assignment = True
        allow_population_by_field_name = True
        use_enum_values = True
