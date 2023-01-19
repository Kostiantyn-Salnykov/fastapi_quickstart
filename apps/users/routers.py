from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.authorization.dependencies import IsAuthenticated, bearer_auth
from apps.CORE.dependencies import get_async_session
from apps.CORE.responses import Responses
from apps.CORE.schemas import JSENDOutSchema
from apps.users.handlers import users_handler
from apps.users.schemas import LoginOutSchema, LoginSchema, TokenRefreshSchema, UserCreateSchema, UserOutSchema

__all__ = ("register_router", "users_router", "tokens_router")

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
    response_model=JSENDOutSchema[UserOutSchema],
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    request: Request,
    data: UserCreateSchema,
    session: AsyncSession = Depends(get_async_session),
) -> JSENDOutSchema[UserOutSchema]:
    """Creates new user."""
    return JSENDOutSchema[UserOutSchema](
        data=await users_handler.create_user(request=request, session=session, data=data),
        message="Created User's details.",
        code=status.HTTP_201_CREATED,
    )


@users_router.get(
    path="/",
    name="whoami",
    summary="Who am I?",
    description="Get user's data from authorization.",
    response_model=JSENDOutSchema[UserOutSchema],
    status_code=status.HTTP_200_OK,
)
async def whoami(request: Request) -> JSENDOutSchema[UserOutSchema]:
    """Gets information about user from authorization."""
    return JSENDOutSchema[UserOutSchema](data=request.user, message="User's data from authorization.")


@tokens_router.post(
    path="/login/", name="login", response_model=JSENDOutSchema[LoginOutSchema], status_code=status.HTTP_200_OK
)
async def login(
    request: Request, data: LoginSchema, session: AsyncSession = Depends(get_async_session)
) -> JSENDOutSchema[LoginOutSchema]:
    return JSENDOutSchema[LoginOutSchema](
        data=await users_handler.login(request=request, session=session, data=data),
        message="Tokens to authenticate user for working with API.",
    )


@tokens_router.put(path="/refresh/", name="refresh", response_model=JSENDOutSchema[LoginOutSchema])
async def refresh(
    request: Request, data: TokenRefreshSchema, session: AsyncSession = Depends(get_async_session)
) -> JSENDOutSchema[LoginOutSchema]:
    return JSENDOutSchema[LoginOutSchema](
        data=await users_handler.refresh(request=request, session=session, data=data),
        message="Tokens to authenticate user for working with API.",
    )
