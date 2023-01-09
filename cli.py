import asyncio
from functools import wraps

import typer

from apps.authorization.managers import AuthorizationManager
from apps.CORE.db import async_session_factory, engine
from loggers import get_logger, setup_logging

setup_logging()  # enable logging inside CLI
logger = get_logger(name=__name__)
auth_manager = AuthorizationManager(engine=engine)


def make_async(func):  # type: ignore
    """Decorator to user Typer commands with asyncio."""

    @wraps(func)
    def wrapper(*args, **kwargs):  # type: ignore
        """Run function with asyncio."""
        return asyncio.run(func(*args, **kwargs))

    return wrapper


app = typer.Typer(name="FastAPI Quickstart CLI", help="Command Line Interface for FastAPI application.")
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
    async with async_session_factory() as session:
        await auth_manager.create_object_permissions(session=session)


@superusers_commands.command(name="setup", help="Creates superusers Permissions, 'Superusers' Group, 'Superuser' Role.")
@make_async
async def setup_superusers() -> None:
    async with async_session_factory() as session:
        await auth_manager.setup_superusers(session=session)


@superusers_commands.command(
    name="create", help="Creates User and assign 'Superusers' Group, 'Superuser' Role and superusers Permissions."
)
@make_async
async def create_superuser(
    first_name: str = typer.Option(
        "Kostiantyn", "--first_name", "-f", prompt="Enter First name", show_default=True, help="First name of user."
    ),
    last_name: str = typer.Option(
        "Salnykov", "--last_name", "-l", prompt="Enter Last name", show_default=True, help="Last name of user."
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
    logger.debug(msg=f"Superuser created successfully ({first_name=}, {last_name=}, {email=}, {password=}).")
    ...  # TODO: Create User, add to `Superusers` Group, add `Superuser` Role, assign Permissions.


if __name__ == "__main__":
    app()
