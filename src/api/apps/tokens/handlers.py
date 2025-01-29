__all__ = (
    "login",
    "refresh",
)
from typing import Annotated

from core.dependencies import get_async_session
from core.dependencies.limiters import Rate, SlidingWindowRateLimiter
from core.enums import RatePeriod
from core.schemas.responses import JSENDResponseSchema
from domain.users.handlers import users_handler
from domain.users.schemas.requests import LoginSchema, TokenRefreshSchema
from domain.users.schemas.responses import LoginOutSchema
from fastapi import Body, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession


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


async def refresh(
    request: Request,
    data: TokenRefreshSchema,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> JSENDResponseSchema[LoginOutSchema]:
    return JSENDResponseSchema[LoginOutSchema](
        data=await users_handler.refresh(request=request, session=session, data=data),
        message="Tokens to authenticate user for working with API.",
    )
