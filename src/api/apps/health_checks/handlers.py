__all__ = ("healthcheck",)
from core.dependencies import AsyncSessionDependency, RedisDependency
from core.enums import JSENDStatus
from fastapi import Request, status
from fastapi.responses import ORJSONResponse
from sqlalchemy import text

from src.settings import Settings


async def healthcheck(
    request: Request,
    redis: RedisDependency,
    async_session: AsyncSessionDependency,
) -> ORJSONResponse:
    """Check that API endpoints work properly.

    Returns:
        ORJSONResponse: json object with JSENDResponseSchema body.
    """
    if Settings.APP_DEBUG:
        async_result = await async_session.execute(statement=text("SELECT true;"))
        data = {
            "redis": await redis.ping(),
            "postgresql_async": async_result.scalar_one(),
        }
    else:
        data = None
    return ORJSONResponse(
        content={
            "status": JSENDStatus.SUCCESS,
            "data": data,
            "message": "Health check.",
            "code": status.HTTP_200_OK,
        },
        status_code=status.HTTP_200_OK,
    )
