import abc
import math
import typing
import urllib.parse

from fastapi import Query, Request

from apps.CORE.schemas import PaginationOutSchema
from apps.CORE.types import ObjectsVar, SchemaType, StrUUID

__all__ = ("PaginationInterface", "LimitOffsetPagination", "NextTokenPagination")


class PaginationInterface(abc.ABC):
    @abc.abstractmethod
    def paginate(
        self,
        request: Request,
        objects: list[ObjectsVar],
        schema: typing.Type[SchemaType],
        total: int,
        endpoint_name: str,
    ) -> PaginationOutSchema[SchemaType]:
        ...


class LimitOffsetPagination(PaginationInterface):
    def __init__(self) -> None:
        """Initializer for BasePagination. Also, setup default values."""
        self.offset = 0
        self.limit = 100

    def __call__(
        self,
        offset: int = Query(default=0, ge=0, description="Number of records to skip."),
        limit: int = Query(default=100, ge=1, le=1000, description="Number of records to return per request."),
    ) -> "LimitOffsetPagination":
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
            str(request.url_for(endpoint_name)) + "?" + urllib.parse.urlencode(query=self.previous())
            if self.offset > 0
            else None
        )
        objects_count = len(objects)
        next_url = (
            str(request.url_for(endpoint_name)) + "?" + urllib.parse.urlencode(query=self.next())
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


class NextTokenPagination(PaginationInterface):
    def __init__(self) -> None:
        self.limit: int = 100

    def __call__(
        self,
        next_token: StrUUID = Query(
            default=None, description="nextToken this is latest `id` of previous result.", alias="nextToken"
        ),
        limit: int = Query(default=100, ge=1, le=1000, description="Number of records to return per request."),
    ) -> "NextTokenPagination":
        """Callable `Depends` class usage."""
        self.next_token = next_token
        self.limit = limit
        return self

    def next(self, next_token: str) -> dict[str, int | str]:
        return {"nextToken": next_token, "pageSize": self.limit}

    def paginate(
        self,
        request: Request,
        objects: list[ObjectsVar],
        schema: typing.Type[SchemaType],
        total: int,
        endpoint_name: str,
    ) -> PaginationOutSchema[SchemaType]:
        objects_count = len(objects)
        has_more = objects_count >= self.limit
        if has_more:
            next_token = objects[-1].id
        else:
            next_token = None

        next_url = (
            str(request.url_for(endpoint_name)) + "?" + urllib.parse.urlencode(query=self.next(next_token=next_token))
            if next_token
            else None
        )

        if total % self.limit == 0:
            pages = total // self.limit
        else:
            pages = total // self.limit + 1

        return PaginationOutSchema[schema](
            objects=(schema.from_orm(obj=obj) for obj in objects),  # type: ignore
            limit=self.limit,
            count=objects_count,
            total_count=total,
            previous_url=None,
            next_token=next_token,
            next_url=next_url,
            pages=pages,
        )
