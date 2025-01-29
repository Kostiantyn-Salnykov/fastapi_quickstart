"""Config file for alembic migrations."""

import asyncio
import pathlib

from alembic import context
from core.custom_logging import get_logger
from core.db.bases import Base, async_engine
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

logger = get_logger(name=__name__)
logger.info("You should import models explicitly to the `env.py` file to allow autogenerate migrations.")

from domain.users.tables import User  # noqa
# from domain.authorization.tables import (
#     Group,
#     GroupRole,
#     GroupUser,
#     Permission,
#     PermissionUser,
#     Role,
#     RolePermission,
#     RoleUser,
# )

tables = ", ".join(list(Base.metadata.tables.keys()))
logger.trace(f"Found these tables in `Base.metadata`: {tables}.")

config = context.config  # settings from alembic.ini file.
target_metadata = Base.metadata  # metadata for models.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    migrations_dir = pathlib.Path(__file__).parent.resolve()
    sql_versions_dir = migrations_dir / "versions_sql"
    if not sql_versions_dir.exists():
        sql_versions_dir.mkdir()

    context.configure(
        url=async_engine.url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        transactional_ddl=False,
        output_buffer=pathlib.Path.open(sql_versions_dir / f"{context.get_head_revision()}.sql", "w"),
        dialect_name="postgresql",
        version_table="migrations",
        transaction_per_migration=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        dialect_name="postgresql",
        dialect_opts={"paramstyle": "named"},
        version_table="migrations",
        transaction_per_migration=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations(connectable) -> None:
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    connectable = context.config.attributes.get("connection", None)  # for pytest-alembic

    if connectable is None:  # without pytest-alembic (local / production)
        connectable = async_engine

    if isinstance(connectable, AsyncEngine):
        asyncio.run(run_async_migrations(connectable=connectable))
    else:
        with connectable.connect() as connection:
            do_run_migrations(connection=connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
