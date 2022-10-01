from fastapi import status

from apps.CORE.enums import JSENDStatus


async def test_healthcheck(async_client, app_fixture):
    response = await async_client.get(url=app_fixture.url_path_for(name="healthcheck"))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "status": JSENDStatus.SUCCESS,
        "data": None,
        "message": "Health check.",
        "code": status.HTTP_200_OK,
    }
