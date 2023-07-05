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
from sqlalchemy.sql import func

import redis.asyncio as aioredis
from settings import Settings

__all__ = (
    "BaseTableModelMixin",
    "UUIDMixin",
    "CreatedAtMixin",
    "UpdatedAtMixin",
    "CreatedUpdatedMixin",
    "NAMING_CONVENTION",
    "Base",
    "async_engine",
    "engine",
    "async_session_factory",
    "session_factory",
    "redis_engine",
)


@declarative_mixin
class BaseTableModelMixin:
    """Mixin for rewrite table name magic method."""

    pattern = re.compile(r"(?<!^)(?=[A-Z])")

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.pattern.sub("_", cls.__name__).lower()

    def to_dict(self) -> dict[str, typing.Any]:
        return self.__dict__


@declarative_mixin
class UUIDMixin:
    """Mixin for rewrite integer id field to uuid4 id field."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid_extensions.uuid7,
        primary_key=True,
    )


@declarative_mixin
class CreatedAtMixin:
    """Mixin for add created_at field."""

    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )


@declarative_mixin
class UpdatedAtMixin:
    """Mixin for add updated_at field."""

    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


@declarative_mixin
class CreatedUpdatedMixin(CreatedAtMixin, UpdatedAtMixin):
    """Mixin for add updated_at and created_at fields."""

    pass


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
