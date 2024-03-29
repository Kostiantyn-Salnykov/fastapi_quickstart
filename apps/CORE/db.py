import datetime
import re
import typing
import uuid

import uuid_extensions
from sqlalchemy import TIMESTAMP, MetaData, create_engine
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import (
    Mapped,
    Session,
    declarative_base,
    declarative_mixin,
    declared_attr,
    mapped_column,
    sessionmaker,
)
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.sql import func

import redis.asyncio as aioredis
from settings import Settings

__all__ = (
    "async_engine",
    "async_session_factory",
    "Base",
    "BaseTableModelMixin",
    "CreatedAtMixin",
    "CreatedUpdatedMixin",
    "engine",
    "NAMING_CONVENTION",
    "redis_engine",
    "session_factory",
    "UpdatedAtMixin",
    "UUIDMixin",
)


@declarative_mixin
class BaseTableModelMixin:
    """Mixin for rewrite table name magic method."""

    pattern = re.compile(r"(?<!^)(?=[A-Z])")

    @declared_attr
    def __tablename__(cls) -> str:
        """Dynamic attribute to create name for table in PostgreSQL.

        Examples:
            class Users -> "users";
            class WishList -> "wish_list";
            class WishTag -> "wish_tag";
        """
        return cls.pattern.sub("_", cls.__name__).lower()

    def to_dict(self) -> dict[str, typing.Any]:
        """Recursively converts DB object instance to python dictionary."""
        result = self.__dict__
        for k, v in result.items():
            if isinstance(v, InstrumentedList):
                # Recursion on joined relationship fields.
                result[k] = [obj.to_dict() for obj in v]
        return result

    def __str__(self) -> str:
        """Default Human representation for Model."""
        return self.__repr__()


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


@declarative_mixin
class CreatedUpdatedMixin(CreatedAtMixin, UpdatedAtMixin):
    """Mixin for adding "updated_at" and "created_at" fields."""

    ...


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",  # Index
    "uq": "uq_%(table_name)s_%(column_0_name)s",  # UniqueConstraint
    "ck": "ck_%(table_name)s_%(constraint_name)s",  # Check
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # ForeignKey
    "pk": "pk_%(table_name)s",  # PrimaryKey
}

Base = declarative_base(cls=BaseTableModelMixin, metadata=MetaData(naming_convention=NAMING_CONVENTION))
async_engine = create_async_engine(url=Settings.POSTGRES_URL_ASYNC, echo=Settings.POSTGRES_ECHO)
engine = create_engine(url=Settings.POSTGRES_URL, echo=Settings.POSTGRES_ECHO)
async_session_factory = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False, future=True)
session_factory = sessionmaker(bind=engine, class_=Session, expire_on_commit=False, future=True)
redis_engine = aioredis.Redis(
    host=Settings.REDIS_HOST,
    port=Settings.REDIS_PORT,
    db=Settings.REDIS_DB,
    password=Settings.REDIS_PASSWORD,
    encoding=Settings.REDIS_ENCODING,
    decode_responses=Settings.REDIS_DECODE_RESPONSES,
    retry_on_timeout=True,
    max_connections=Settings.REDIS_POOL_MAX_CONNECTIONS,
    client_name="FastAPI_client",
    username=Settings.REDIS_USER,
    ssl=Settings.REDIS_SECURE,
    # ssl_keyfile=PROJECT_BASE_DIR / "redis/certs/redis.key",
    # ssl_certfile=PROJECT_BASE_DIR / "redis/certs/redis.crt",
    # ssl_cert_reqs="required",
    # ssl_ca_certs=PROJECT_BASE_DIR / "redis/certs/ca.crt",
)
