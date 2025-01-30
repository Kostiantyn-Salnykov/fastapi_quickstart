__all__ = (
    "BaseTableModelMixin",
    "CreatedAtMixin",
    "CreatedUpdatedMixin",
    "UUIDMixin",
    "UpdatedAtMixin",
)
import datetime
import re
import uuid

import uuid_extensions
from sqlalchemy import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    declarative_mixin,
    declared_attr,
    mapped_column,
    validates,
)
from sqlalchemy.sql import func

from core.annotations import SchemaType
from core.helpers import get_utc_timezone


@declarative_mixin
class BaseTableModelMixin:
    """Mixin for rewrite table name magic method."""

    pattern = re.compile("((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))")

    @declared_attr
    def __tablename__(cls) -> str:
        """Dynamic attribute to create name for table in PostgreSQL.

        Examples:
            class Users -> "users";
            class WishList -> "wish_list";
            class WishTag -> "wish_tag";
        """
        return cls.pattern.sub(r"_\1", cls.__name__).lower()

    def __str__(self) -> str:
        """Default Human representation for Model."""
        return self.__repr__()

    def to_schema(self, schema_class: SchemaType) -> SchemaType:
        return SchemaType.model_validate(self, schema=schema_class, from_attributes=True)


@declarative_mixin
class UUIDMixin:
    """Mixin for rewrite integer id field to uuid4 id field."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid_extensions.uuid7,
        primary_key=True,
    )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(id="{self.id}")'


@declarative_mixin
class CreatedAtMixin:
    """Mixin for adding "created_at" field."""

    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )

    @validates("created_at")
    def validate_tz_info(self, _: str, value: datetime.datetime) -> datetime.datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=get_utc_timezone())
        return value


@declarative_mixin
class UpdatedAtMixin:
    """Mixin for adding "updated_at" field."""

    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @validates("updated_at")
    def validate_tz_info(self, _: str, value: datetime.datetime) -> datetime.datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=get_utc_timezone())
        return value


@declarative_mixin
class CreatedUpdatedMixin(CreatedAtMixin, UpdatedAtMixin):
    """Mixin for adding "updated_at" and "created_at" fields."""

    ...
