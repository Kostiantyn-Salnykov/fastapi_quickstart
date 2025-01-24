from core.schemas.requests import BaseRequestSchema


class Filter(BaseRequestSchema):
    field: str
    operation: str
    value: str | list[str]


class Metadata(BaseRequestSchema):
    filters: list[Filter]
