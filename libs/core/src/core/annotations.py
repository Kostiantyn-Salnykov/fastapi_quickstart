import datetime
import typing
import uuid

from core.db.bases import Base
from pydantic import BaseModel
from sqlalchemy import Column

StrOrUUID = str | uuid.UUID
StrOrNone = str | None
ListOfAny = list[typing.Any]
DictStrOfAny = dict[str, typing.Any]
DictIntOfAny = dict[int, typing.Any]
ModelInstance = typing.TypeVar("ModelInstance", bound=Base)
SchemaInstance = typing.TypeVar("SchemaInstance", bound=BaseModel)
ModelType = type[ModelInstance]
SchemaType = type[SchemaInstance]
ModelOrNone = ModelInstance | None
ModelListOrNone = list[ModelInstance] | None
ModelColumnInstance = typing.TypeVar("ModelColumnInstance", bound=Column)
ResultObject = typing.TypeVar("ResultObject", bound=dict[str, None | str | int | float | dict | list])
DatetimeOrNone = datetime.datetime | None
CountModelListResult = tuple[int, list[ModelInstance]]
