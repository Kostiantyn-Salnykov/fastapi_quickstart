__all__ = ("Projection",)
import enum
import typing

from fastapi import Body, Request
from pydantic import Field
from sqlalchemy.orm import Load, undefer
from sqlalchemy.orm.strategy_options import _AbstractLoad

from apps.CORE.custom_types import ModelType, SchemaType
from apps.CORE.schemas.requests import BaseRequestSchema
from loggers import get_logger

_logger = get_logger(name=__name__)


class ProjectionMode(str, enum.Enum):
    INCLUDE = "INCLUDE"
    EXCLUDE = "EXCLUDE"


class ProjectionRequest(BaseRequestSchema):
    fields: list[str] | typing.Literal["*"] = Field(
        default=...,
        title="Fields",
        description="List of fields to include / exclude from result.",
    )
    mode: ProjectionMode = Field(
        default=ProjectionMode.INCLUDE,
        title="Mode",
        description="Select between include / exclude.",
    )


class Projection:
    _wildcard_symbol = "*"

    def __init__(self, model: ModelType, schema: SchemaType) -> None:
        self.model = model
        self.schema = schema
        self.aliases_mapping = self.schema.collect_aliases()

    @property
    def query(self) -> Load | _AbstractLoad:
        return self._projection

    async def __call__(  # noqa: PLR0912
        self,
        request: Request,
        projection: typing.Annotated[
            ProjectionRequest,
            Body(
                alias="projection",
                title="Projection",
                description="You can choose what fields to include OR exclude from response.",
                examples=[None, {"fields": "*", "mode": "INCLUDE"}, {"fields": "*", "mode": "EXCLUDE"}],
                openapi_examples={
                    "Include all": {
                        "summary": "Include",
                        "description": "Include all fields",
                        "value": {"fields": "*", "mode": "INCLUDE"},
                    },
                    "Exclude all": {
                        "summary": "Exclude",
                        "description": "Exclude all fields",
                        "value": {"fields": "*", "mode": "EXCLUDE"},
                    },
                },
            ),
        ] = None,
    ) -> typing.Self:
        if not request.state.sorting:
            msg = "You can't use Projection without `Sorting`."
            raise NotImplementedError(msg)
        if not projection:
            _logger.debug(
                msg=f"Projection | __call__ | Projection not provided, using `undefer({self._wildcard_symbol})`.",
            )
            request.state.projection = undefer(self._wildcard_symbol)
            result = undefer(self._wildcard_symbol)
            self._projection = result
            return self

        if projection.fields in (self._wildcard_symbol, [self._wildcard_symbol]):
            _logger.debug(
                msg=f"Projection | __call__ | {projection.fields=}, running wildcard ({self._wildcard_symbol}) "
                f"flow.",
            )
            match projection.mode:
                case ProjectionMode.INCLUDE:
                    _logger.debug(
                        msg=f"Projection | __call__ | {projection.mode=}, using `undefer({self._wildcard_symbol})`.",
                    )
                    result = undefer(self._wildcard_symbol)
                case ProjectionMode.EXCLUDE:
                    _logger.debug(
                        msg=f"Projection | __call__ | {projection.mode=}, using `load_only` by fields from sorting.",
                    )
                    result = []
                    # Fields, that used in sorting cannot be excluded from result.
                    for field in request.state.sorting.raw_sorting:
                        field_name = self.aliases_mapping.get(field, "...")
                        if hasattr(self.model, field_name):
                            result.append(getattr(self.model, field_name))
                    result = Load(entity=self.model).load_only(*result)
                case _:
                    result = ...

            self._projection = result
            request.state.projection = self
            return self

        match projection.mode:
            case ProjectionMode.INCLUDE:
                _logger.debug(
                    msg=f"Projection | __call__ | {projection.mode=}, running `load_only` on {projection.fields} + "
                    f"{request.state.sorting.raw_sorting}.",
                )
                results = []
                for field in projection.fields + request.state.sorting.raw_sorting:
                    field_name = self.aliases_mapping.get(field, "...")
                    if hasattr(self.model, field_name):
                        results.append(getattr(self.model, field_name))

                if results:
                    result = Load(entity=self.model).load_only(*results)
                else:
                    result = Load(entity=self.model).load_only(self.model.id)
            case ProjectionMode.EXCLUDE:
                _logger.debug(msg=f"Projection | __call__ | {projection.mode=}, running exclude flow.")
                _logger.debug("Projection | __call__ | Including `id` to response.")
                result = undefer(self.model.id)
                for field in projection.fields:
                    field_name = self.aliases_mapping.get(field, "...")
                    if hasattr(self.model, field_name):
                        attr = getattr(self.model, field_name)
                        if attr.primary_key or field_name in request.state.sorting.raw_sorting:
                            _logger.debug(
                                msg=f"Projection | __call__ | Skipping `{field_name}` because it's PK or included "
                                f"in sorting.",
                            )
                            continue
                        _logger.debug(msg=f"Projection | __call__ | Excluding `{attr}` from response.")
                        result = result.defer(attr)
            case _:
                result = ...

        self._projection = result
        request.state.projection = self
        return self
