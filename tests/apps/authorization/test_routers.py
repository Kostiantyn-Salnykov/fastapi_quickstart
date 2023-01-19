import pytest
from faker import Faker
from fastapi import FastAPI, status
from httpx import AsyncClient

from apps.CORE.enums import JSENDStatus
from apps.CORE.tables import Group, Role
from tests.apps.conftest import assert_is_uuid, assert_jsend_response
from tests.apps.CORE.factories import GroupFactory, RoleFactory


class TestGroupsRouter:
    async def test_create_group_201_title_only(
        self, async_client: AsyncClient, app_fixture: FastAPI, faker: Faker
    ) -> None:
        title = faker.pystr(max_chars=256)

        response = await async_client.post(url=app_fixture.url_path_for(name="create_group"), json={"title": title})

        assert_jsend_response(
            response=response,
            http_code=status.HTTP_201_CREATED,
            status=JSENDStatus.SUCCESS,
            message="Group object created successfully.",
            code=status.HTTP_201_CREATED,
        )
        response_data = response.json()["data"]
        assert_is_uuid(val=response_data["id"])
        assert response_data["roles"] == []

    async def test_create_group_201_with_roles(
        self, async_client: AsyncClient, app_fixture: FastAPI, faker: Faker
    ) -> None:
        roles: list[Role] = RoleFactory.create_batch(size=2)
        title = faker.pystr(max_chars=256)

        response = await async_client.post(
            url=app_fixture.url_path_for(name="create_group"),
            json={"title": title, "roles_ids": [str(role.id) for role in roles]},
        )

        assert_jsend_response(
            response=response,
            http_code=status.HTTP_201_CREATED,
            status=JSENDStatus.SUCCESS,
            message="Group object created successfully.",
            code=status.HTTP_201_CREATED,
        )
        response_data = response.json()["data"]
        assert_is_uuid(val=response_data["id"])
        assert response_data["roles"] == [
            {
                "id": str(role.id),
                "permissions": [
                    {"id": str(permission.id), "objectName": permission.object_name, "action": permission.action}
                    for permission in role.permissions
                ],
                "title": role.title,
            }
            for role in roles
        ]

    async def test_create_group_404_roles_not_fround(
        self, async_client: AsyncClient, app_fixture: FastAPI, faker: Faker
    ) -> None:
        roles_ids = [faker.uuid4(), faker.uuid4()]
        title = faker.pystr(max_chars=256)

        response = await async_client.post(
            url=app_fixture.url_path_for(name="create_group"),
            json={"title": title, "roles_ids": roles_ids},
        )

        assert_jsend_response(
            response=response,
            http_code=status.HTTP_404_NOT_FOUND,
            status=JSENDStatus.FAIL,
            message="Role(s) not found.",
            code=status.HTTP_404_NOT_FOUND,
        )
        response_data = response.json()["data"]
        for role_id in response_data:
            assert role_id in roles_ids

    async def test_list_groups_200(self, async_client: AsyncClient, app_fixture: FastAPI, faker: Faker) -> None:
        groups: list[Group] = GroupFactory.create_batch(size=2)
        expected_result = [
            {
                "id": str(group.id),
                "title": group.title,
                "roles": [
                    {
                        "id": str(role.id),
                        "title": role.title,
                        "permissions": [
                            {
                                "id": str(permission.id),
                                "objectName": permission.object_name,
                                "action": permission.action,
                            }
                            for permission in role.permissions
                        ],
                    }
                    for role in group.roles
                ],
            }
            for group in groups
        ]

        response = await async_client.get(
            url=app_fixture.url_path_for(name="list_groups"),
        )

        assert_jsend_response(
            response=response,
            http_code=status.HTTP_200_OK,
            status=JSENDStatus.SUCCESS,
            message="Paginated list of Group objects.",
            code=status.HTTP_200_OK,
        )
        response_objects = response.json()["data"]["objects"]
        for group in expected_result:
            assert group in response_objects

    async def test_read_group_404(self, async_client: AsyncClient, app_fixture: FastAPI, faker: Faker) -> None:
        group_id = faker.uuid4()

        response = await async_client.get(
            url=app_fixture.url_path_for(name="read_group", id=group_id),
        )

        assert_jsend_response(
            response=response,
            http_code=status.HTTP_404_NOT_FOUND,
            status=JSENDStatus.FAIL,
            message="Group not found.",
            code=status.HTTP_404_NOT_FOUND,
            data=None,
        )

    async def test_read_group_200(self, async_client: AsyncClient, app_fixture: FastAPI, faker: Faker) -> None:
        group: Group = GroupFactory()
        expected_result = {
            "id": str(group.id),
            "title": group.title,
            "roles": [
                {
                    "id": str(role.id),
                    "title": role.title,
                    "permissions": [
                        {
                            "id": str(permission.id),
                            "objectName": permission.object_name,
                            "action": permission.action,
                        }
                        for permission in role.permissions
                    ],
                }
                for role in group.roles
            ],
        }

        response = await async_client.get(
            url=app_fixture.url_path_for(name="read_group", id=str(group.id)),
        )

        assert_jsend_response(
            response=response,
            http_code=status.HTTP_200_OK,
            status=JSENDStatus.SUCCESS,
            message="Group details.",
            code=status.HTTP_200_OK,
            data=expected_result,
        )

    @pytest.mark.debug()
    async def test_update_group_200_title(self, async_client: AsyncClient, app_fixture: FastAPI, faker: Faker) -> None:
        old_title = "test"
        new_title = faker.pystr(max_chars=256)
        group: Group = GroupFactory(title=old_title, roles=[])
        updated_group = {"id": str(group.id), "roles": group.roles, "title": new_title}
        old_response = await async_client.get(
            url=app_fixture.url_path_for(name="read_group", id=str(group.id)),
        )
        assert old_response.json()["data"]["title"] == old_title

        response = await async_client.patch(
            url=app_fixture.url_path_for(name="update_group", id=str(group.id)), json={"title": new_title}
        )

        assert_jsend_response(
            response=response,
            http_code=status.HTTP_200_OK,
            status=JSENDStatus.SUCCESS,
            message="Group details.",
            code=status.HTTP_200_OK,
            data=updated_group,
        )

    async def test_update_group_200_title_with_roles(
        self, async_client: AsyncClient, app_fixture: FastAPI, faker: Faker
    ) -> None:
        old_title = "test"
        new_title = faker.pystr(max_chars=256)
        new_roles: list[Role] = RoleFactory.create_batch(size=2, permissions=[])
        group: Group = GroupFactory(title=old_title, roles=[])
        updated_group = {
            "id": str(group.id),
            "roles": [{"id": str(role.id), "title": role.title, "permissions": role.permissions} for role in new_roles],
            "title": new_title,
        }
        old_response = await async_client.get(
            url=app_fixture.url_path_for(name="read_group", id=str(group.id)),
        )
        assert old_response.json()["data"]["title"] == old_title
        assert old_response.json()["data"]["roles"] == []

        response = await async_client.patch(
            url=app_fixture.url_path_for(name="update_group", id=str(group.id)),
            json={"title": new_title, "roles_ids": [str(role.id) for role in new_roles]},
        )

        assert_jsend_response(
            response=response,
            http_code=status.HTTP_200_OK,
            status=JSENDStatus.SUCCESS,
            message="Group details.",
            code=status.HTTP_200_OK,
            data=updated_group,
        )

    @pytest.mark.debug()
    async def test_update_group_404_not_found_roles(
        self, async_client: AsyncClient, app_fixture: FastAPI, faker: Faker
    ) -> None:
        old_title = "test"
        new_title = faker.pystr(max_chars=256)
        fake_role_id, fake_role_id_2 = faker.uuid4(), faker.uuid4()
        role: Role = RoleFactory()
        group: Group = GroupFactory(title=old_title, roles=[role])
        old_response = await async_client.get(
            url=app_fixture.url_path_for(name="read_group", id=str(group.id)),
        )
        assert old_response.json()["data"]["title"] == old_title

        response = await async_client.patch(
            url=app_fixture.url_path_for(name="update_group", id=str(group.id)),
            json={
                "title": new_title,
                "roles_ids": [str(role_id) for role_id in (role.id, fake_role_id, fake_role_id_2)],
            },
        )

        assert_jsend_response(
            response=response,
            http_code=status.HTTP_404_NOT_FOUND,
            status=JSENDStatus.FAIL,
            message="Role(s) not found.",
            code=status.HTTP_404_NOT_FOUND,
        )
        assert set(response.json()["data"]) == {fake_role_id, fake_role_id_2}

    @pytest.mark.debug()
    async def test_update_group_400_nothing_to_update(
        self, async_client: AsyncClient, app_fixture: FastAPI, faker: Faker
    ) -> None:
        group: Group = GroupFactory()

        response = await async_client.patch(
            url=app_fixture.url_path_for(name="update_group", id=str(group.id)), json={}
        )

        assert_jsend_response(
            response=response,
            http_code=status.HTTP_400_BAD_REQUEST,
            status=JSENDStatus.FAIL,
            message="Nothing to update.",
            code=status.HTTP_400_BAD_REQUEST,
            data=None,
        )
