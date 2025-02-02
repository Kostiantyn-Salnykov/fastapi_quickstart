import asyncio
import typing
from collections.abc import Callable
from functools import wraps

import typer
from core.custom_logging import get_logger, setup_logging
from core.db.bases import async_engine, async_session_factory

from src.api.authorization.managers import AuthorizationManager

setup_logging()  # enable logging inside CLI
logger = get_logger(name=__name__)
auth_manager = AuthorizationManager(engine=async_engine)


Function = typing.TypeVar("Function", bound=Callable[..., typing.Any])


def make_async(func: Function) -> Function:  # type: ignore
    """Decorator to user Typer commands with asyncio."""

    @wraps(func)
    def wrapper(*args, **kwargs):  # type: ignore  # noqa: ANN202
        """Run function with asyncio."""
        return asyncio.run(func(*args, **kwargs))

    return wrapper


app = typer.Typer(
    name="FastAPI Quickstart CLI",
    help="Command Line Interface for FastAPI application.",
)
authorization_commands = typer.Typer(name="auth", help="Commands for 'Authorization' app.")
permissions_commands = typer.Typer(name="permissions", help="Manage Permissions objects in db.")
superusers_commands = typer.Typer(name="superusers", help="Manage superusers.")
app.add_typer(typer_instance=authorization_commands)
authorization_commands.add_typer(typer_instance=permissions_commands)
authorization_commands.add_typer(typer_instance=superusers_commands)


# app
# --> auth
# --|--> permissions
# --|--|--> setup (`poetry run python cli.py auth permissions setup`)
# --|--> superusers
# --|--|--> setup (`poetry run python cli.py auth superusers setup`)
# --|--|--> create (`poetry run python cli.py auth superusers create`)


@permissions_commands.command(name="setup", help="Creates Permissions for all models.")
@make_async
async def setup_permissions() -> None:
    """Scan all tables and creates Permissions for them (CRUD action for every table)."""
    async with async_session_factory() as session:
        await auth_manager.create_object_permissions(session=session)


@superusers_commands.command(
    name="setup",
    help="Creates superusers Permissions, 'Superusers' Group, 'Superuser' Role.",
)
@make_async
async def setup_superusers() -> None:
    """Creates standard Groups/Roles/Permissions.

    Note:
        Group: `Superusers`
        Role: `Superuser`
        Permission: object_name="__all__" with actions="create|read|update|delete"
    """
    async with async_session_factory() as session:
        await auth_manager.setup_superusers(session=session)


@superusers_commands.command(
    name="create",
    help="Create User and assign 'Superusers' Group, 'Superuser' Role and superusers Permissions.",
)
@make_async
async def create_superuser(
    first_name: str = typer.Option(
        "Kostiantyn",
        "--first_name",
        "-f",
        prompt="Enter First name",
        show_default=True,
        help="First name of user.",
    ),
    last_name: str = typer.Option(
        "Salnykov",
        "--last_name",
        "-l",
        prompt="Enter Last name",
        show_default=True,
        help="Last name of user.",
    ),
    email: str = typer.Option(
        "kostiantyn.salnykov@gmail.com",
        "--email",
        "-e",
        prompt="Enter Email",
        show_default=True,
        help="Email of user.",
    ),
    password: str = typer.Option(
        ...,
        "--password",
        "-p",
        prompt="Enter Password",
        confirmation_prompt=True,
        hide_input=True,
        help="Password for user.",
    ),
) -> None:
    """Create superuser with provided inputs."""
    logger.debug(msg=f"Superuser created successfully ({first_name=}, {last_name=}, {email=}, {password=}).")
    ...  # TODO: Create User, add to `Superusers` Group, add `Superuser` Role, assign Permissions.


if __name__ == "__main__":
    app()
