"""Config file for alembic migrations."""
import pathlib
from logging.config import fileConfig

from alembic import context

from apps.CORE.db import Base, engine

# You should import models explicitly to this file, to allow autogenerate migrations.
from apps.CORE.tables import User  # noqa
from apps.CORE.tables import (  # noqa
    Group,
    GroupRole,
    GroupUser,
    Permission,
    PermissionUser,
    Role,
    RolePermission,
    RoleUser,
)
from apps.wishmaster.models import Category, Tag, Wish, WishList, WishTag  # noqa

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    MIGRATIONS_DIR = pathlib.Path(__file__).parent.resolve()
    SQL_VERSIONS_DIR = MIGRATIONS_DIR / "sql_versions"
    if not SQL_VERSIONS_DIR.exists():
        SQL_VERSIONS_DIR.mkdir()

    context.configure(
        url=engine.url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        transactional_ddl=False,
        output_buffer=open(SQL_VERSIONS_DIR / f"{context.get_head_revision()}.sql", "w"),
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = context.config.attributes.get("connection", None)  # for pytest-alembic

    if connectable is None:  # without pytest-alembic (local / production)
        connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
