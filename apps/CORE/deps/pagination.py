import math
import typing
import urllib.parse

from fastapi import Query, Request

from apps.CORE.schemas import PaginationOutSchema
from apps.CORE.types import ObjectsVar, SchemaType

__all__ = ("BasePagination",)


# TODO: Think about `page` query instead of `offset`.
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
            request.url_for(endpoint_name) + "?" + urllib.parse.urlencode(query=self.previous())
            if self.offset > 0
            else None
        )
        objects_count = len(objects)
        next_url = (
            request.url_for(endpoint_name) + "?" + urllib.parse.urlencode(query=self.next())
            if objects_count == self.limit and objects_count != total
            else None
        )
        return PaginationOutSchema[schema](
            objects=(schema.from_orm(obj=obj) for obj in objects),  # type: ignore
            offset=self.offset,
            limit=self.limit,
            count=objects_count,
            total_count=total,
            previous_url=previous_url,
            next_url=next_url,
            page=int(math.floor(self.offset / self.limit) + 1),  # calculate current page.
            pages=int(math.ceil(total / self.limit)),  # calculate total numbed of pages.
        )
