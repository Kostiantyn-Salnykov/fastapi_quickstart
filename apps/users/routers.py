from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.authorization.dependencies import IsAuthenticated, bearer_auth
from apps.CORE.deps import get_async_session
from apps.CORE.deps.limiters import Rate, SlidingWindowRateLimiter
from apps.CORE.enums import RatePeriod
from apps.CORE.responses import Responses
from apps.CORE.schemas.responses import JSENDResponseSchema
from apps.users.handlers import users_handler
from apps.users.schemas.requests import LoginSchema, TokenRefreshSchema, UserCreateSchema
from apps.users.schemas.responses import LoginOutSchema, UserResponseSchema

__all__ = (
    "register_router",
    "tokens_router",
    "users_router",
)

register_router = APIRouter(prefix="/users", tags=["users"])
users_router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(bearer_auth), Depends(IsAuthenticated())],
    responses=Responses.AUTH,
)
tokens_router = APIRouter(tags=["tokens"])


@register_router.post(
    path="/",
    name="create_user",
    summary="Registration",
    description="Create user and get details.",
    response_model=JSENDResponseSchema[UserResponseSchema],
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
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
    session: AsyncSession = Depends(get_async_session),
) -> JSENDResponseSchema[UserResponseSchema]:
    """Creates new user."""
    return JSENDResponseSchema[UserResponseSchema](
        data=await users_handler.create_user(request=request, session=session, data=data),
        message="Created User details.",
        code=status.HTTP_201_CREATED,
    )


@users_router.get(
    path="/",
    name="whoami",
    summary="Who am I?",
    description="Get user's data from authorization.",
    response_model=JSENDResponseSchema[UserResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def whoami(request: Request) -> JSENDResponseSchema[UserResponseSchema]:
    """Gets information about user from authorization."""
    return JSENDResponseSchema[UserResponseSchema](data=request.user, message="User's data from authorization.")


@tokens_router.post(
    path="/login/",
    name="login",
    response_model=JSENDResponseSchema[LoginOutSchema],
    status_code=status.HTTP_200_OK,
)
async def login(
    request: Request,
    data: Annotated[
        LoginSchema,
        Body(
            openapi_examples={
                "Success": {
                    "value": {"email": "kostiantyn.salnykov@gmail.com", "password": "!QAZxsw2"},
                },
                "Fail": {
                    "value": {"email": "john.doe@gmail.com", "password": "123445678"},
                },
            },
        ),
    ],
    _limiter: Annotated[None, (Depends(SlidingWindowRateLimiter(rate=Rate(number=3, period=RatePeriod.MINUTE))))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> JSENDResponseSchema[LoginOutSchema]:
    return JSENDResponseSchema[LoginOutSchema](
        data=await users_handler.login(request=request, session=session, data=data),
        message="Tokens to authenticate user for working with API.",
    )


@tokens_router.put(path="/refresh/", name="refresh", response_model=JSENDResponseSchema[LoginOutSchema])
async def refresh(
    request: Request,
    data: TokenRefreshSchema,
    session: AsyncSession = Depends(get_async_session),
) -> JSENDResponseSchema[LoginOutSchema]:
    return JSENDResponseSchema[LoginOutSchema](
        data=await users_handler.refresh(request=request, session=session, data=data),
        message="Tokens to authenticate user for working with API.",
    )
