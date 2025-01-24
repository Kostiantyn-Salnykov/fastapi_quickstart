import base64
import json
import operator
import typing

from core.annotations import (
    DictStrOfAny,
    ModelInstance,
    ModelOrNone,
    ModelType,
    SchemaInstance,
    SchemaType,
    StrOrNone,
)
from core.custom_logging import get_logger
from core.helpers import ExtendedJSONDecoder, ExtendedJSONEncoder
from core.schemas.requests import BaseRequestSchema
from core.schemas.responses import PaginationResponseSchema
from fastapi import Body, Request
from pydantic import Field
from sqlalchemy import and_, or_
from sqlalchemy.sql.elements import ColumnElement

_logger = get_logger(name=__name__)


class PaginationRequestSchema(BaseRequestSchema):
    """RequestSchema for pagination."""

    next_token: StrOrNone = Field(default=None, description="nextToken from a previous result.", alias="nextToken")
    limit: int = Field(default=100, ge=1, le=1000, description="Number of records to return per request.")


class Pagination:
    """Pagination dependency class definition."""

    def __init__(self, model: ModelType, schema: SchemaType) -> None:
        self.model = model
        self.schema = schema

    async def __call__(
        self,
        request: Request,
        pagination: typing.Annotated[
            PaginationRequestSchema,
            Body(
                alias="pagination",
                title="Pagination",
                description="You can paginate result objects by `nextToken` and set a `limit` number of returned "
                "objects.",
                examples=[None, {"nextToken": None, "limit": 100}, {"nextToken": None, "limit": 10}],
                openapi_examples={
                    "Limit100": {
                        "summary": "100",
                        "description": "Limit for 100 objects.",
                        "value": {"nextToken": None, "limit": 100},
                    },
                    "Limit10": {
                        "summary": "10",
                        "description": "Limit for 10 objects.",
                        "value": {"nextToken": None, "limit": 10},
                    },
                },
            ),
        ] = None,
    ) -> typing.Self:
        """Dependency method."""
        if not pagination:
            pagination = PaginationRequestSchema()
        if not request.state.sorting:
            msg = "You can't use Pagination without `Sorting`."
            raise NotImplementedError(msg)

        self.next_token = pagination.next_token
        self.limit = pagination.limit
        request.state.pagination = self
        self.request = request
        return self

    def paginate(
        self,
        objects: list[ModelInstance],
        total: int,
    ) -> PaginationResponseSchema[SchemaInstance]:
        """Returns paginated ResponseSchema from the list of objects."""
        _logger.debug(msg=f"Pagination | paginate | {objects=}, {total=}).")
        next_token = self.create_next_token(latest_object=objects[-1] if objects else None, objects_count=len(objects))

        return PaginationResponseSchema[self.schema](
            objects=(self.schema.from_model(obj=obj) for obj in objects),  # type: ignore
            limit=self.limit,
            total_count=total,
            next_token=next_token,
        )

    def create_next_token(self, latest_object: ModelOrNone, objects_count: int) -> StrOrNone:
        """Generate next_token for subsequent requests."""
        _logger.debug(msg=f"Pagination | create_next_token | {latest_object=}, {objects_count=}.")
        if objects_count < self.limit:
            next_token = None
            _logger.debug(msg=f"Pagination | create_next_token | {objects_count=} < {self.limit=} => {next_token=}.")
        else:
            next_token_struct = [
                {
                    "field": sort_field.element.key,
                    "value": getattr(latest_object, sort_field.element.key),
                    "order": str(sort_field.expression).split()[-1].lower(),
                }
                for sort_field in self.request.state.sorting.query
            ]
            data: str = json.dumps(next_token_struct, cls=ExtendedJSONEncoder)
            _logger.debug(msg=f"Pagination | create_next_token | {data=}.")
            next_token: str = base64.urlsafe_b64encode(data.encode(encoding="utf-8")).decode(encoding="utf-8")
            _logger.debug(msg=f"Pagination | create_next_token | {next_token=}.")
        return next_token

    def read_next_token(self, next_token: StrOrNone) -> list[DictStrOfAny] | None:
        """Read & parse next_token from request."""
        _logger.debug(msg=f"Pagination | read_next_token | {next_token=}.")
        if not next_token:
            return None

        try:
            next_token_bytes: bytes = base64.urlsafe_b64decode(next_token.encode("utf-8"))
            _logger.debug(msg=f"Pagination | read_next_token | {next_token_bytes=}.")
            next_token: list[DictStrOfAny] = json.loads(next_token_bytes, cls=ExtendedJSONDecoder)
        except Exception as error:
            _logger.warning(msg=f"Pagination | read_next_token | Error parsing `nextToken` | {error}")
            next_token = None

        _logger.debug(msg=f"Pagination | read_next_token | {next_token=}.")
        return next_token

    def get_query(self, next_token: StrOrNone) -> ColumnElement[bool] | None:
        """Returns SQLAlchemy ready query for pagination."""
        _logger.debug(msg=f"Pagination | get_next_query | {next_token=}.")
        next_token = self.read_next_token(next_token=next_token)
        if not next_token:
            return None

        pagination_conditions = []
        previous_conditions = []
        for next_token_field in next_token:
            field, value, order = (
                next_token_field["field"],
                next_token_field["value"],
                next_token_field["order"],
            )
            operation = operator.gt if order == "asc" else operator.lt
            pagination_conditions.append(and_(*previous_conditions, operation(getattr(self.model, field), value)))
            previous_conditions.append(getattr(self.model, field) == value)

        return or_(*pagination_conditions)
