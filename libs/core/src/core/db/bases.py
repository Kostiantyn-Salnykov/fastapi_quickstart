__all__ = (
    "CASCADES",
    "NAMING_CONVENTION",
    "Base",
    "async_engine",
    "async_session_factory",
    "redis_engine",
)

from core.db.mixins import BaseTableModelMixin
from core.db.settings import db_settings
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import (
    declarative_base,
)

import redis.asyncio as aioredis

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",  # Index
    "uq": "uq_%(table_name)s_%(column_0_name)s",  # UniqueConstraint
    "ck": "ck_%(table_name)s_%(constraint_name)s",  # Check
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # ForeignKey
    "pk": "pk_%(table_name)s",  # PrimaryKey
}
CASCADES = {"ondelete": "CASCADE", "onupdate": "CASCADE"}

Base = declarative_base(cls=BaseTableModelMixin, metadata=MetaData(naming_convention=NAMING_CONVENTION))
async_engine = create_async_engine(url=db_settings.APP_RDMS_URL, echo=db_settings.APP_RDMS_ECHO)
async_session_factory = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False, future=True)
redis_engine = aioredis.Redis(
    host=db_settings.REDIS_HOST,
    port=db_settings.REDIS_PORT,
    db=db_settings.REDIS_DB,
    password=db_settings.REDIS_PASSWORD,
    encoding=db_settings.REDIS_ENCODING,
    decode_responses=db_settings.REDIS_DECODE_RESPONSES,
    retry_on_timeout=True,
    max_connections=db_settings.REDIS_POOL_MAX_CONNECTIONS,
    client_name="FastAPI_client",
    username=db_settings.REDIS_USER,
    ssl=db_settings.REDIS_SECURE,
    # ssl_keyfile=PROJECT_BASE_DIR / "redis/certs/redis.key",
    # ssl_certfile=PROJECT_BASE_DIR / "redis/certs/redis.crt",
    # ssl_cert_reqs="required",
    # ssl_ca_certs=PROJECT_BASE_DIR / "redis/certs/ca.crt",
)
