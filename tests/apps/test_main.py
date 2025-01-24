from core.enums import JSENDStatus
from fastapi import FastAPI, status
from httpx import AsyncClient


async def test_healthcheck(async_client: AsyncClient, app_fixture: FastAPI) -> None:
    response = await async_client.get(url=app_fixture.url_path_for("healthcheck"))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "status": JSENDStatus.SUCCESS,
        "data": {
            "postgresql_async": True,
            "postgresql_sync": True,
            "redis": True,
        },
        "message": "Health check.",
        "code": status.HTTP_200_OK,
    }
