import typing

from fastapi import Body, Request
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, model_validator
from sqlalchemy import BinaryExpression
from sqlalchemy.orm import ColumnProperty, InstrumentedAttribute

from apps.CORE.custom_types import ModelType, SchemaType, StrOrNone
from apps.CORE.enums import FOps
from apps.CORE.exceptions import BackendError
from apps.CORE.schemas.requests import BaseRequestSchema
from settings import Settings

TypeA = typing.TypeVar("TypeA")
FilterValue: typing.TypeAlias = list[int | float | bool | StrOrNone] | int | float | bool | StrOrNone
TypeValue = typing.TypeVar("TypeValue")


def get_sqlalchemy_where_operations_mapper(operation_type: FOps) -> str:
    match operation_type:
        case operation_type.EQUAL:
            return "__eq__"
        case operation_type.NOT_EQUAL:
            return "__ne__"
        case operation_type.GREATER:
            return "__gt__"
        case operation_type.GREATER_OR_EQUAL:
            return "__ge__"
        case operation_type.LESS:
            return "__lt__"
        case operation_type.LESS_OR_EQUAL:
            return "__le__"
        case operation_type.IN:
            return "in_"
        case operation_type.NOT_IN:
            return "not_in"
        case operation_type.LIKE:
            return "like"
        case operation_type.ILIKE:
            return "ilike"
        case operation_type.STARTSWITH:
            return "startswith"
        case operation_type.ENDSWITH:
            return "endswith"
        case operation_type.ISNULL:
            return "isnull"
        case operation_type.NOT_NULL:
            return "notnull"
        case _:  # pragma: no cover
            return "__eq__"  # default


class QueryFilter(BaseModel, typing.Generic[TypeA]):
    model_config = ConfigDict(
        populate_by_name=True, json_schema_extra={"examples": [{"field": "title", "operation": "=", "value": "Test"}]}
    )

    field: str = Field(default=..., alias="f")
    operation: FOps = Field(default=FOps.EQ, alias="o")
    value: TypeA = Field(default=..., alias="v")

    @model_validator(mode="after")
    def validate_obj(self) -> typing.Self:
        operation: FOps = self.operation
        match operation:
            case FOps.IN | FOps.NOT_IN:
                if not isinstance(self.value, list):
                    raise BackendError(
                        message=f"Filters error. For operation '{operation.value}', the value must be a list (Array[])."
                    )
            case FOps.ISNULL | FOps.NOT_NULL:
                self.value = None
            case _ as operation:
                if isinstance(self.value, list):
                    raise BackendError(
                        message=f"Filters error. For operation '{operation.value}', the value cannot be a list "
                        f"(Array[])."
                    )
        return self


class F:
    """F (Filter) class settings."""

    def __init__(self, query_field_name: str, possible_operations: list[FOps], value_type: TypeValue) -> None:
        self._name = query_field_name
        self._operations = possible_operations
        self._type: TypeValue = value_type

    def create_model(self) -> type[QueryFilter[TypeValue]]:
        """Dynamically generates Pydantic model to validate filter via TypeValue."""
        return QueryFilter[self._type]

    @property
    def name(self) -> str:
        """Get name of field query parameter (can be alias)."""
        return self._name


class FiltrationRequest(BaseRequestSchema):
    field: str = Field(default=..., title="Field", alias="f", description="Field name.", example="title")
    operation: FOps = Field(default=FOps.EQ, title="Operation", alias="o", description="Operation type.", example="=")
    value: FilterValue = Field(default=..., title="Value", alias="v", description="Value.", example="Test")


class Filtration:
    def __init__(self, model: type[ModelType], schema: type[SchemaType], filters: list[F]) -> None:
        self.model = model
        self.schema = schema
        self.filters: list[F] = filters
        self.filters_mapping = self.collect_filtering()
        self.aliases_mapping = self.schema.collect_aliases()

    @property
    def query(self):
        return self._filtration

    def __iter__(self):
        yield from self.query

    async def __call__(
        self,
        request: Request,
        filtration: typing.Annotated[
            list[FiltrationRequest],
            Body(
                alias="filtration",
                title="Filtration",
                description="You can filter by multiple fields (Actually this applied as `AND` logic in result query).",
            ),
        ] = None,
    ) -> typing.Self:
        result: list[BinaryExpression] = []
        if filtration:
            query_filters_list = self.parse_query_filters(filters_list=filtration)
            result.extend(op for op in self.construct_sqlalchemy_operation(query_filters=query_filters_list))

        request.state.filtration = result
        self._filtration = result
        return self

    def collect_filtering(self) -> dict[str, type[QueryFilter[TypeValue]] | None]:
        fields: dict[str, type[QueryFilter[TypeValue]] | None] = {}
        # populate fields with aliases or names and empty None value
        for name, field in self.schema.model_fields.items():
            if field.alias:
                fields.update({field.alias: None})
            else:
                fields.update({name: None})
        # populate fields with filters
        for f in self.filters:
            model_field_name = f.name
            if model_field_name in fields:
                fields[model_field_name] = f.create_model()

        return fields

    def parse_query_filters(self, filters_list: list[FiltrationRequest]) -> list[QueryFilter[list[str] | StrOrNone]]:
        query_filters_list: list[QueryFilter[list[str] | StrOrNone]] = []
        try:
            for fltr in filters_list:
                fltr_adptr = TypeAdapter(QueryFilter[FilterValue])
                fltr_schema = fltr_adptr.validate_python(fltr.model_dump())
                if fltr_schema.field in self.filters_mapping:
                    try:
                        filter_model = self.filters_mapping[fltr_schema.field]
                        query_filters_list.append(filter_model.model_validate(fltr.model_dump()))
                    except Exception as error:
                        raise BackendError(
                            data={"Parsed filter (DEBUG)": fltr_schema.model_dump()} if Settings.DEBUG else None,
                            message=f"Can't parse filter value of '{fltr_schema.field}'. Check validity of "
                            f"filter Object{{}} or a possibility filtering by this field.",
                        ) from error
        except ValidationError as error:
            raise BackendError(
                data={"Parsed JSON (DEBUG)": filters_list} if Settings.DEBUG else None,
                message="Invalid 'filters' Array[Filter{}]. Every filter should be an Object{} with three fields: "
                "'field' or 'f', 'operator' or 'o', 'value' or 'v'.",
            ) from error
        return query_filters_list

    def construct_sqlalchemy_operation(
        self, query_filters: list[QueryFilter[list[str] | StrOrNone]]
    ) -> typing.Generator[BinaryExpression, None, None]:
        for filter_schema in query_filters:
            column = getattr(self.model, self.aliases_mapping.get(filter_schema.field), None)
            if isinstance(column, InstrumentedAttribute) and isinstance(column.property, ColumnProperty):
                selected_operation = get_sqlalchemy_where_operations_mapper(operation_type=filter_schema.operation)
                operation: BinaryExpression = getattr(column, selected_operation)(filter_schema.value)
                yield operation
