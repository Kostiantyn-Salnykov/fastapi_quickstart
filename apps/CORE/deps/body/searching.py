import enum
import typing

from fastapi import Body, Request
from pydantic import Field
from sqlalchemy import TextClause, text

from apps.CORE.custom_types import ModelColumnInstance, ModelType, SchemaType
from apps.CORE.schemas.requests import BaseRequestSchema
from loggers import get_logger

_logger = get_logger(name=__name__)


class SearchingMode(str, enum.Enum):
    WEB = "WEB"
    PHRASE = "PHRASE"
    PLAIN = "PLAIN"


class SearchingRequest(BaseRequestSchema):
    text: str = Field(max_length=128, description="Text that will be used in search.")
    mode: SearchingMode = Field(default=SearchingMode.PLAIN, description="Mode for text search.")
    language: typing.Literal["simple", "english", "ukrainian"] = Field(
        default="simple",
        description="Language that will be selected for `to_tsvector`.",
    )
    fields: list[str] = Field(
        default_factory=list,
        description="Fields for searching. If multiple provided, it used with `OR` logic.",
    )


class Searching:
    def __init__(
        self,
        model: ModelType,
        schema: SchemaType,
        available_columns: list[ModelColumnInstance] | None = None,
    ) -> None:
        self.model = model
        self.schema = schema
        self.aliases_mapping = self.schema.collect_aliases()
        self.available_columns_names = [col.key for col in available_columns or []]

    async def __call__(
        self,
        request: Request,
        searching: typing.Annotated[
            SearchingRequest,
            Body(
                alias="searching",
                title="Searching",
                description="You can search by one or many fields.",
                examples=[
                    None,
                    {"text": "Wishlist", "mode": "PLAIN", "language": "english", "fields": ["title", "description"]},
                ],
                openapi_examples={
                    "Empty": {"summary": "No searching", "description": "", "value": None},
                    "Search by one field": {
                        "summary": "Multiple fields search",
                        "description": "",
                        "value": {
                            "text": "Wishlist",
                            "mode": "PLAIN",
                            "language": "english",
                            "fields": ["title"],
                        },
                    },
                },
            ),
        ] = None,
    ) -> typing.Self:
        search_queries: list[TextClause] = []

        if not searching:
            _logger.debug(msg=f"{self.__class__.__name__} | __call__ | {searching=}. Skipped.")
            self._searching = search_queries
            return self

        _logger.debug(
            msg=f'{self.__class__.__name__} | __call__ | text="{searching.text}", mode={searching.mode}, '
            f'language="{searching.language}", fields={searching.fields}.',
        )
        search_mode = self.get_postgresql_search_method(mode=searching.mode)

        for field in searching.fields:
            column_name = self.aliases_mapping.get(field, field)
            if hasattr(self.model, column_name) and column_name in self.available_columns_names:
                column = getattr(self.model, column_name)
                query = text(f"to_tsvector({column.name}) @@ {search_mode}(:query)").params(query=searching.text)
                search_queries.append(query)

        self._searching = search_queries
        request.state.searching = self
        return self

    @property
    def query(self) -> list[TextClause]:
        return self._searching

    def __iter__(self) -> typing.Iterator[list[TextClause]]:
        yield from self.query

    def get_postgresql_search_method(self, mode: SearchingMode) -> str:
        _default = "plainto_tsquery"

        match mode:
            case SearchingMode.PLAIN:
                result = "plainto_tsquery"
            case SearchingMode.PHRASE:
                result = "phraseto_tsquery"
            case SearchingMode.WEB:
                result = "websearch_to_tsquery"
            case _:
                result = _default

        _logger.debug(msg=f"{self.__class__.__name__} | get_postgresql_search_method | {mode=} => {result=}.")
        return result
