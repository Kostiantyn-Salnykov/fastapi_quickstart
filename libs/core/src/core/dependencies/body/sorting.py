import typing

from core.annotations import ModelColumnInstance, ModelType, SchemaType
from core.custom_logging import get_logger
from fastapi import Body, Request
from sqlalchemy import UnaryExpression

_logger = get_logger(name=__name__)


class Sorting:
    """Sorting dependency class definition."""

    def __init__(
        self,
        model: ModelType,
        schema: SchemaType,
        default_sorting: list[str] | None = None,
        available_columns: list[ModelColumnInstance] | None = None,
    ) -> None:
        self.model = model
        self.schema = schema
        self.aliases_mapping = self.schema.collect_aliases()
        self._default_sorting = default_sorting or ["-id"]  # If no provided, sort by `id` DESC.
        self.available_columns_names = [col.key for col in available_columns or []]

    @property
    def query(self) -> list[UnaryExpression]:
        """Returns SQLAlchemy ready query for sorting."""
        return self._sorting

    @property
    def raw_sorting(self) -> list[str]:
        """Returns sorting query for usage inside projection."""
        return self._raw_sorting

    async def __call__(
        self,
        request: Request,
        sorting: typing.Annotated[
            list[str] | None,
            Body(
                alias="sorting",
                title="Sorting",
                description="You can sort by one or multiple fields. "
                "\n\n**Examples**: "
                '\n\n`"sorting": ["-id"]` (_This will sort `id` by DESC order._) - **This is a default behavior.**'
                '\n\n`"sorting": ["title", "-createdAt"]` (_This will sort `title` ASC, then `createdAt` DESC order._)'
                "\n\n**Warning** `-id` automatically appends to end of  sorting list."
                "\n\n**P.S.** Order of `sorting` query parameters are matter!",
                examples=[None, ["-id"]],
            ),
        ] = None,
    ) -> typing.Self:
        """Dependency method."""
        _logger.debug(msg=f"{self.__class__.__name__} | __call__ | {sorting=}.")
        if not sorting:
            _logger.debug(
                msg=f"{self.__class__.__name__} | __call__ | Sorting is empty, using `{self._default_sorting}`.",
            )
            sorting = self._default_sorting
        else:
            _logger.debug(
                msg=f"{self.__class__.__name__} | __call__ | Sorting is not empty. Checking that the latest one field "
                f"is `-id`.",
            )
            sorting.extend(self._default_sorting) if sorting[-1] != self._default_sorting[-1] else ...

        raw_sorting = []
        result = []
        for column in sorting:
            raw_column = column.strip().removeprefix("-").removeprefix("+")
            # retrieve real column name by alias, or skip (by default)
            raw_column = self.aliases_mapping.get(raw_column, raw_column)
            if hasattr(self.model, raw_column) and raw_column in self.available_columns_names:
                raw_sorting.append(raw_column)
                ordering_method = "desc" if column.startswith("-") else "asc"  # Choose method to use: .acs() OR .desc()
                col_attr = getattr(self.model, raw_column)  # e.g. Get model attribute dynamically: Model.<raw_column>
                result.append(getattr(col_attr, ordering_method)())  # e.g. Model.<raw_column>.desc()

        self._sorting = result
        self._raw_sorting = raw_sorting
        _logger.debug(msg=f"{self.__class__.__name__} | __call__ | {self.query=}, {self.raw_sorting=}.")
        request.state.sorting = self
        return self
