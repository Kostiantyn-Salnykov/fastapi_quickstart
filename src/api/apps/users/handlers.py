__all__ = (
    "registration",
    "whoami",
)
from typing import Annotated

from core.dependencies import AsyncSessionDependency
from core.schemas.responses import JSENDResponseSchema
from domain.users.handlers import users_handler
from domain.users.schemas.requests import UserCreateSchema
from domain.users.schemas.responses import UserResponseSchema
from fastapi import Body, Request, status


async def registration(
    request: Request,
    data: Annotated[
        UserCreateSchema,
        Body(
            openapi_examples={
                "Kostiantyn Salnykov": {
                    "value": {
                        "firstName": "Kostiantyn",
                        "lastName": "Salnykov",
                        "email": "kostiantyn.salnykov@gmail.com",
                        "password": "!QAZxsw2",
                    },
                },
                "Invalid email": {
                    "value": {"firstName": "John", "lastName": "Doe", "email": "fake@fake!", "password": "12345678"},
                },
                "Short password": {
                    "value": {"firstName": "John", "lastName": "Doe", "email": "john.doe@gmail.com", "password": "123"},
                },
            },
        ),
    ],
    session: AsyncSessionDependency,
) -> JSENDResponseSchema[UserResponseSchema]:
    """Creates new user."""
    return JSENDResponseSchema[UserResponseSchema](
        data=await users_handler.create_user(request=request, session=session, data=data),
        message="Created User details.",
        code=status.HTTP_201_CREATED,
    )


async def whoami(request: Request) -> JSENDResponseSchema[UserResponseSchema]:
    """Gets information about user from authorization."""
    return JSENDResponseSchema[UserResponseSchema](data=request.user, message="User's data from authorization.")
