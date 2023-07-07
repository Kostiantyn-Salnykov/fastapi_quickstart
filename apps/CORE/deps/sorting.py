from fastapi import Query
from sqlalchemy import UnaryExpression

from apps.CORE.types import ModelColumnVar, ModelType, SchemaType

__all__ = ("BaseSorting",)


class BaseSorting:
    def __init__(
        self,
        model: type[ModelType],
        schema: type[SchemaType],
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
            "\n\n**Warning** `-id` automatically appends to end of  sorting list."
            "\n\n**P.S.** Order of `sorting` query parameters are matter!",
        ),
    ) -> list[UnaryExpression]:
        return self.build_sorting(sorting=sorting)

    def collect_aliases(self) -> dict[str, str]:
        result = {}  # <alias_name>: <real_name>
        for _, field in self.schema.__fields__.items():
            if field.has_alias:
                result.update({field.alias: field.name})
        return result

    def build_sorting(self, sorting: list[str] | None) -> list[UnaryExpression]:
        sorting.append("-id") if isinstance(sorting, list) else ...  # add sort by `id` in DESC order.
        aliases_map = self.collect_aliases()
        result = []
        for column in sorting or ["-id"]:  # If no provided, sort by `id` DESC.
            raw_column = column.strip().removeprefix("-").removeprefix("+")
            # retrieve real column name by alias, or skip (by default)
            raw_column = aliases_map.get(raw_column, raw_column)
            if hasattr(self.model, raw_column) and raw_column in self.available_columns_names:
                ordering_method = "desc" if column.startswith("-") else "asc"  # Choose method to use: .acs() OR .desc()
                col_attr = getattr(self.model, raw_column)  # e.g. Get model attribute dynamically: Model.<raw_column>
                result.append(getattr(col_attr, ordering_method)())  # e.g. Model.<raw_column>.desc()
        return result
