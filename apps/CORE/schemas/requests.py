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

    @classmethod
    def collect_aliases(cls: type[BaseModel]) -> dict[str, str]:
        result = {}  # <alias_name>: <real_name> OR <real_name>: <real_name>
        for name, field in cls.model_fields.items():
            if field.alias:
                result.update({field.alias: name})
            else:
                result.update({name: name})
        return result
