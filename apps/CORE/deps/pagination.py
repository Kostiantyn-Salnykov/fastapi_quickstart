import abc
import math

from fastapi import Query, Request

from apps.CORE.schemas.responses import PaginationResponse
from apps.CORE.types import ObjectsVar, SchemaType, StrUUID

__all__ = ("PaginationInterface", "LimitOffsetPagination", "NextTokenPagination")


class PaginationInterface(abc.ABC):
    @abc.abstractmethod
    def paginate(
        self,
        request: Request,
        objects: list[ObjectsVar],
        schema: type[SchemaType],
        total: int,
        endpoint_name: str,
    ) -> PaginationResponse[SchemaType]:
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

    def paginate(
        self,
        request: Request,
        objects: list[ObjectsVar],
        schema: type[SchemaType],
        total: int,
        endpoint_name: str,
    ) -> PaginationResponse[SchemaType]:
        return PaginationResponse[schema](
            objects=(schema.from_orm(obj=obj) for obj in objects),  # type: ignore
            offset=self.offset,
            limit=self.limit,
            total_count=total,
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
        return {"nextToken": next_token, "limit": self.limit}

    def paginate(
        self,
        request: Request,
        objects: list[ObjectsVar],
        schema: type[SchemaType],
        total: int,
        endpoint_name: str,
    ) -> PaginationResponse[SchemaType]:
        objects_count = len(objects)
        next_token = objects[-1].id if objects_count >= self.limit else None
        pages = total // self.limit if total % self.limit == 0 else total // self.limit + 1

        return PaginationResponse[schema](
            objects=(schema.from_orm(obj=obj) for obj in objects),  # type: ignore
            limit=self.limit,
            total_count=total,
            next_token=next_token,
            pages=pages,
        )
