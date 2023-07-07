import string
import typing

import orjson
from fastapi import Query, Request
from pydantic import Field, ValidationError, parse_obj_as, validator
from pydantic.generics import GenericModel
from sqlalchemy import BinaryExpression
from sqlalchemy.orm import ColumnProperty, InstrumentedAttribute

from apps.CORE.enums import FOps
from apps.CORE.exceptions import BackendError
from apps.CORE.types import ModelType, SchemaType
from settings import Settings

__all__ = (
    "get_sqlalchemy_where_operations_mapper",
    "QueryFilter",
    "F",
    "BaseFilters",
)


TypeA = typing.TypeVar("TypeA")
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


class QueryFilter(GenericModel, typing.Generic[TypeA]):
    field: str = Field(default=..., alias="f")
    operation: FOps = Field(default=FOps.EQ, alias="o")
    value: TypeA = Field(default=..., alias="v")

    class Config:
        allow_population_by_field_name = True
        schema_extra = {"examples": [{"test": "test"}]}

    @validator("value")
    def validate_obj(cls, v, values: dict[str, typing.Any]):
        operation: FOps = values.get("operation", FOps.EQ)
        match operation:
            case FOps.IN | FOps.NOT_IN:
                if not isinstance(v, list):
                    raise BackendError(
                        message=f"Filters error. For operation '{operation.value}', the value must be a list (Array[])."
                    )
            case FOps.ISNULL | FOps.NOT_NULL:
                return None
            case _ as operation:
                if isinstance(v, list):
                    raise BackendError(
                        message=f"Filters error. For operation '{operation.value}', the value cannot be a list "
                        f"(Array[])."
                    )
        return v


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


class BaseFilters:
    def __init__(self, *, model: type[ModelType], schema: type[SchemaType], filters: list[F]) -> None:
        self.model: type[ModelType] = model
        self.schema: type[SchemaType] = schema
        self.filters: list[F] = filters
        self.filters_mapping = self.collect_filtering()
        self.aliases_mapping = self.collect_aliases()

    async def __call__(
        self,
        request: Request,
        json_filters: str
        | None = Query(
            default=None,
            alias="filters",
            title="Filtering system.",
            description=str(
                string.Template(
                    """You can filter by multiple fields (Actually this applied as `AND` logic in result query).
                \n\n**Structure**: Base64 URL encoded stringified JSON Array[Object{}]
                \n\n**Possible Operations** (`"o"`, `"operation"`): $OPERATIONS
                \n\n**Examples**:
                \n\nfilters=`""` (No filters, same as omit the `&filters`);
                \n\nfilters=`[{"f": "title", "o": "=", "v": "test"}]` (Filter by 'title' field where it is a 'test');
                \n\nfilters=`[{"f": "status", "o": "in", "v": ["CREATED", "IN PROGRESS"]}]`
                (Filter by 'status' field where it has 'CREATED' and 'IN PROGRESS' values);
                \n\nfilters=`[{"f": "description", "o": "!=", "v": null},
                {"f": "title", "o": "startswith", "v": "test"}]`
                (Filter by 'description' field where it is not NULL `AND` by title which startswith 'test')
            """
                ).safe_substitute(OPERATIONS=", ".join(f"`{op.value}`" for op in FOps))
            ),
        ),
    ) -> list[BinaryExpression]:
        result: list[BinaryExpression] = []
        if json_filters:
            filters_list = self.parse_json_filters(json_filters=json_filters)
            query_filters_list = self.parse_query_filters(filters_list=filters_list)
            result.extend(op for op in self.construct_sqlalchemy_operation(query_filters=query_filters_list))
        return result

    def collect_filtering(self) -> dict[str, type[QueryFilter[TypeValue]] | None]:
        fields: dict[str, type[QueryFilter[TypeValue]] | None] = {}
        # populate fields with aliases or names and empty None value
        for _, field in self.schema.__fields__.items():
            if field.has_alias:
                fields.update({field.alias: None})
            else:
                fields.update({field.name: None})
        # populate fields with filters
        for f in self.filters:
            model_field_name = f.name
            if model_field_name in fields:
                fields[model_field_name] = f.create_model()

        return fields

    def collect_aliases(self) -> dict[str, str]:
        result = {}  # <alias_name>: <real_name> OR <real_name>: <real_name>
        for _, field in self.schema.__fields__.items():
            if field.has_alias:
                result.update({field.alias: field.name})
            else:
                result.update({field.name: field.name})
        return result

    def parse_json_filters(self, json_filters: str) -> list[dict[str, typing.Any]]:
        try:
            filters_list: list[dict[str, typing.Any]] = orjson.loads(json_filters)
        except orjson.JSONDecodeError as error:
            raise BackendError(
                message="Cannot parse 'filters' query parameter. It should be a valid urlencoded JSON string."
            ) from error
        else:
            return filters_list

    def parse_query_filters(
        self, filters_list: list[dict[str, typing.Any]]
    ) -> list[QueryFilter[list[str] | str | None]]:
        query_filters_list: list[QueryFilter[list[str] | str | None]] = []
        try:
            for fltr in filters_list:
                fltr_schema: QueryFilter[list[str] | str | None] = parse_obj_as(
                    QueryFilter[list[str] | str | None], fltr
                )
                if fltr_schema.field in self.filters_mapping:
                    try:
                        query_filters_list.append(parse_obj_as(self.filters_mapping[fltr_schema.field], fltr))
                    except Exception as error:
                        raise BackendError(
                            data={"Parsed filter (DEBUG)": fltr_schema.dict()} if Settings.DEBUG else None,
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
        self, query_filters: list[QueryFilter[list[str] | str | None]]
    ) -> typing.Generator[BinaryExpression, None, None]:
        for filter_schema in query_filters:
            column = getattr(self.model, self.aliases_mapping.get(filter_schema.field), None)
            if isinstance(column, InstrumentedAttribute) and isinstance(column.property, ColumnProperty):
                selected_operation = get_sqlalchemy_where_operations_mapper(operation_type=filter_schema.operation)
                operation: BinaryExpression = getattr(column, selected_operation)(filter_schema.value)
                yield operation
