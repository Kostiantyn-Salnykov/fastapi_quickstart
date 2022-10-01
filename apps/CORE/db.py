import re
import uuid

from sqlalchemy import TIMESTAMP, Column, MetaData, create_engine, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, declarative_base, declarative_mixin, declared_attr, sessionmaker
from sqlalchemy.sql import func

from settings import Settings


@declarative_mixin
class TableNameMixin:
    """Mixin for rewrite table name magic method."""

    pattern = re.compile(r"(?<!^)(?=[A-Z])")

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.pattern.sub("_", cls.__name__).lower()


@declarative_mixin
class UUIDMixin:
    """Mixin for rewrite integer id field to uuid4 id field."""

    id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        primary_key=True,
    )


@declarative_mixin
class CreatedAtMixin:
    """Mixin for add created_at field."""

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )


@declarative_mixin
class UpdatedAtMixin:
    """Mixin for add updated_at field."""

    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
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

Base = declarative_base(cls=TableNameMixin, metadata=MetaData(naming_convention=NAMING_CONVENTION))
async_engine = create_async_engine(url=Settings.POSTGRES_URL_ASYNC, echo=Settings.POSTGRES_ECHO)
engine = create_engine(url=Settings.POSTGRES_URL, echo=Settings.POSTGRES_ECHO)
async_session_factory = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)
session_factory = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
