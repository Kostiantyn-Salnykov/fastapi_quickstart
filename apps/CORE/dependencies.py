import math
import typing
import urllib.parse

import aioredis
import orjson
from fastapi import Query, Request
from pydantic import Field, ValidationError, parse_obj_as, validator
from pydantic.generics import GenericModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import ColumnProperty, InstrumentedAttribute, Session
from sqlalchemy.sql.elements import BinaryExpression, UnaryExpression

from apps.CORE.db import async_session_factory, redis, session_factory
from apps.CORE.enums import FOps
from apps.CORE.exceptions import BackendException
from apps.CORE.handlers import integrity_error_handler
from apps.CORE.schemas import ObjectsVar, PaginationOutSchema
from apps.CORE.types import ModelColumnVar, ModelType, SchemaType
from loggers import get_logger
from settings import Settings

logger = get_logger(name=__name__)


class BasePagination:
    def __init__(self) -> None:
        """Initializer for BasePagination. Also, setup default values."""
        self.offset = 0
        self.limit = 100

    def __call__(
        self,
        offset: int = Query(default=0, ge=0, description="Number of records to skip."),
        limit: int = Query(default=100, ge=1, le=1000, description="Number of records to return per request."),
    ) -> "BasePagination":
        """Callable `Depends` class usage."""
        self.offset = offset
        self.limit = limit
        return self

    def next(self) -> dict[str, int]:
        return {"offset": self.offset + self.limit, "limit": self.limit}

    def previous(self) -> dict[str, int]:
        return {"offset": val if (val := self.offset - self.limit) >= 0 else 0, "limit": self.limit}

    def paginate(
        self,
        request: Request,
        objects: list[ObjectsVar],
        schema: typing.Type[SchemaType],
        total: int,
        endpoint_name: str,
    ) -> PaginationOutSchema[SchemaType]:
        previous_url = (
            request.url_for(name=endpoint_name) + "?" + urllib.parse.urlencode(query=self.previous())
            if self.offset > 0
            else None
        )
        next_url = (
            request.url_for(name=endpoint_name) + "?" + urllib.parse.urlencode(query=self.next())
            if len(objects) == self.limit
            else None
        )
        return PaginationOutSchema[schema](
            objects=(schema.from_orm(obj=obj) for obj in objects),  # type: ignore
            offset=self.offset,
            limit=self.limit,
            count=len(objects),
            total_count=total,
            previous_url=previous_url,
            next_url=next_url,
            page=int(math.floor(self.offset / self.limit) + 1),  # calculate current page.
            pages=int(math.ceil(total / self.limit)),  # calculate total numbed of pages.
        )


class BaseSorting:
    def __init__(
        self,
        model: typing.Type[ModelType],
        schema: typing.Type[SchemaType],
        available_columns: list[ModelColumnVar] | None = None,
    ):
        self.model = model
        self.schema = schema
        self.available_columns = available_columns or []
        self.available_columns_names = [col.key for col in self.available_columns]

    def __call__(
        self,
        sorting: list[str] = Query(
            default=None,
            title="Sorting system.",
            description="You can sort by one or multiple fields. "
            "\n\n**Examples**: "
            "\n\n`&sorting=field_name` (_This will sort `field_name` by ASC._)"
            "\n\n`&sorting=field_one&sorting=-field_two` (_This will sort `field_one` ASC, then `field_two` DESC._)"
            "\n\n**P.S.** Order of `sorting` query parameters are matter!",
            examples={
                "no sorting": {
                    "summary": "No sorting.",
                    "description": "",
                    "value": [],
                },
                "-createdAt": {
                    "summary": "-createdAt",
                    "description": "Sort by 'createdAt' DESC.",
                    "value": ["-createdAt"],
                },
                "createdAt": {
                    "summary": "createdAt",
                    "description": "Sort by 'createdAt' ASC.",
                    "value": ["createdAt"],
                },
            },
        ),
    ) -> list[UnaryExpression]:
        return self.build_sorting(sorting=sorting)

    def collect_aliases(self) -> dict[str, str]:
        result = {}  # <alias_name>: <real_name>
        for field_name, field in self.schema.__fields__.items():
            if field.has_alias:
                result.update({field.alias: field.name})
        return result

    def build_sorting(self, sorting: list[str]) -> list[UnaryExpression]:
        aliases_map = self.collect_aliases()
        result = []
        for column in sorting or ["-created_at"]:  # If no provided, sort by `created_at` DESC.
            raw_column = column.strip().removeprefix("-").removeprefix("+")
            # retrieve real column name by alias, or skip (by default)
            raw_column = aliases_map.get(raw_column, raw_column)
            if hasattr(self.model, raw_column) and raw_column in self.available_columns_names:
                ordering_method = "desc" if column.startswith("-") else "asc"  # Choose method to use: .acs() OR .desc()
                col_attr = getattr(self.model, raw_column)  # e.g. Get model attribute dynamically: Model.<raw_column>
                result.append(getattr(col_attr, ordering_method)())  # e.g. Model.<raw_column>.desc()
        return result


async def get_async_session() -> typing.AsyncGenerator[AsyncSession, None]:  # pragma: no cover
    """Creates FastAPI dependency for generation of SQLAlchemy AsyncSession.

    Yields:
        AsyncSession: SQLAlchemy AsyncSession.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except IntegrityError as error:
            await session.rollback()
            integrity_error_handler(error=error)
        finally:
            await session.close()


def get_session() -> typing.Generator[Session, None, None]:
    """Creates FastAPI dependency for generation of SQLAlchemy Session.

    Yields:
        Session: SQLAlchemy Session.
    """
    with session_factory() as session:
        try:
            yield session
            session.commit()
        except IntegrityError as error:
            session.rollback()
            integrity_error_handler(error=error)
        finally:
            session.close()


async def get_redis() -> typing.AsyncGenerator[aioredis.Redis, None]:
    async with redis.client() as conn:
        try:
            yield conn
        except Exception as error:
            logger.warning(msg=error)
        finally:
            await conn.close()


def get_sqlalchemy_where_operations_mapper(operation_type: FOps) -> str:
    match operation_type:
        case operation_type.EQUAL:
            return "__eq__"
        case operation_type.NOT_EQUAL:
            return "__ne__"
        case operation_type.GREATER:
            return "__gt__"
        case operation_type.GREATER_OR_EQUAL:
            return "__gt__"
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
        case _:
            return "__eq__"  # default


TypeA = typing.TypeVar("TypeA")
TypeValue = typing.TypeVar("TypeValue")


class QueryFilter(GenericModel, typing.Generic[TypeA]):
    field: str = Field(default=..., alias="f")
    operation: FOps = Field(default="=", alias="o")
    value: TypeA = Field(default=..., alias="v")

    class Config:
        allow_population_by_field_name = True

    @validator("value")
    def validate_obj(cls, v, values: dict):
        operation = values.get("operation", "=")
        if operation in {"in", "notin"}:
            if not isinstance(v, list):
                raise BackendException(
                    message=f"Filters error. For operation '{operation}', the value must be a list (Array[])."
                )
        elif operation in {"isnull", "notnull"}:
            return None
        return v


class F:
    """F (Filter) class settings."""

    def __init__(self, query_field_name: str, possible_operations: list[FOps], value_type: TypeValue) -> None:
        self._name = query_field_name
        self._operations = possible_operations
        self._type: TypeValue = value_type

    def create_model(self) -> typing.Type[QueryFilter[TypeValue]]:
        """Dynamically generates Pydantic model to validate filter via TypeValue."""
        return QueryFilter[self._type]

    @property
    def name(self) -> str:
        """Get name of field query parameter (can be alias)."""
        return self._name


class BaseFilters:
    def __init__(self, *, model: typing.Type[ModelType], schema: typing.Type[SchemaType], filters: list[F]) -> None:
        self.model: typing.Type[ModelType] = model
        self.schema: typing.Type[SchemaType] = schema
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
            description="You can filter by multiple fields." "\n\n TODO: WRITE",
            examples={
                "no filters": {"summary": "No filters.", "description": "", "value": None},
                "title": {
                    "summary": 'title = "test"',
                    "description": "Filter by 'title' field where it is a 'test'.",
                    "value": '[{"f": "title", "o": "=", "v": "test"}]',
                },
                "description": {
                    "summary": "'description' IS NOT NULL",
                    "description": "Filter by 'description' field where it is not NULL.",
                    "value": '[{"f": "description", "o": "!=", "v": null}]',
                },
                "status": {
                    "summary": "'status' IN ['CREATED', 'IN PROGRESS']",
                    "description": "Filter by 'status' field where it has 'CREATED' and 'IN PROGRESS' values.",
                    "value": '[{"f": "status", "o": "in", "v": ["CREATED", "IN PROGRESS"]}]',
                },
            },
        ),
    ) -> list[BinaryExpression]:
        result = []
        if json_filters:
            filters_list = self.parse_json_filters(json_filters=json_filters)
            query_filters_list = self.parse_query_filters(filters_list=filters_list)
            result.extend((op for op in self.construct_sqlalchemy_operation(query_filters=query_filters_list)))
        return result

    def collect_filtering(self) -> dict[str, typing.Type[QueryFilter[TypeValue]] | None]:
        fields: dict[str, typing.Type[QueryFilter[TypeValue]] | None] = {}
        # populate fields with aliases or names and empty None value
        for field_name, field in self.schema.__fields__.items():
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
        for field_name, field in self.schema.__fields__.items():
            if field.has_alias:
                result.update({field.alias: field.name})
            else:
                result.update({field.name: field.name})
        return result

    def parse_json_filters(self, json_filters: str) -> list[dict[str, typing.Any]]:
        try:
            filters_list: list[dict[str, typing.Any]] = orjson.loads(json_filters)
        except orjson.JSONDecodeError:
            raise BackendException(
                message="Cannot parse 'filters' query parameter. It should be a valid urlencoded JSON string."
            )
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
                    except Exception:
                        raise BackendException(
                            data={"Parsed filter (DEBUG)": fltr_schema.dict()} if Settings.DEBUG else None,
                            message=f"Can't parse filter value of '{fltr_schema.field}'. Check validity of "
                            f"filter Object{{}} or a possibility filtering by this field.",
                        )
        except ValidationError:
            raise BackendException(
                data={"Parsed JSON (DEBUG)": filters_list} if Settings.DEBUG else None,
                message="Invalid 'filters' Array[Filter{}]. Every filter should be an Object{} with three fields: "
                "'field' or 'f', 'operator' or 'o', 'value' or 'v'.",
            )
        return query_filters_list

    def construct_sqlalchemy_operation(
        self, query_filters: list[QueryFilter[list[str] | str | None]]
    ) -> typing.Generator[BinaryExpression, None, None]:
        for filter_schema in query_filters:
            column = getattr(self.model, self.aliases_mapping.get(filter_schema.field), None)
            if isinstance(column, InstrumentedAttribute):
                if isinstance(column.property, ColumnProperty):
                    selected_operation = get_sqlalchemy_where_operations_mapper(operation_type=filter_schema.operation)
                    operation: BinaryExpression = getattr(column, selected_operation)(filter_schema.value)
                    yield operation
