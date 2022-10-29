import pytest
from faker import Faker
from pydantic import BaseModel
from pytest_mock import MockerFixture
from sqlalchemy.exc import IntegrityError

from apps.CORE.db import Base
from apps.CORE.dependencies import BasePagination, BaseSorting, get_async_session, get_session


class TestBasePagination:
    def setup_method(self) -> None:
        self.pagination = BasePagination()

    def test__init___(self) -> None:
        assert self.pagination.offset == 0
        assert self.pagination.limit == 100

    @pytest.mark.parametrize(
        argnames=("offset", "limit"),
        argvalues=(
            (0, 10),
            (1, 5),
            (100, 1000),
            (10000, 123),
        ),
    )
    def test__call__(self, offset: int, limit: int) -> None:
        result = self.pagination(offset=offset, limit=limit)

        assert isinstance(self.pagination, BasePagination)
        assert self.pagination == result
        assert self.pagination.offset == offset
        assert self.pagination.limit == limit

    def test_next(self, faker: Faker) -> None:
        offset = faker.pyint(min_value=0, max_value=100000)
        limit = faker.pyint(min_value=1, max_value=1000)
        pagination = self.pagination(offset=offset, limit=limit)
        expected_result = {"offset": offset + limit, "limit": limit}

        result = pagination.next()

        assert result == expected_result

    def test_previous_plus(self, faker: Faker) -> None:
        offset = faker.pyint(min_value=1, max_value=100000)
        limit = faker.pyint(min_value=1, max_value=1000)
        pagination = self.pagination(offset=offset, limit=limit)
        expected_result = {"offset": offset - limit, "limit": limit}

        result = pagination.previous()

        assert result == expected_result

    def test_previous_zero(self, faker: Faker) -> None:
        offset = faker.pyint(min_value=0, max_value=0)
        limit = faker.pyint(min_value=1, max_value=1000)
        pagination = self.pagination(offset=offset, limit=limit)
        expected_result = {"offset": 0, "limit": limit}

        result = pagination.previous()

        assert result == expected_result

    def test_get_paginated_response(self, faker: Faker, mocker: MockerFixture):
        domain = faker.url()
        limit: int = faker.pyint(min_value=10, max_value=1000)
        offset: int = faker.pyint(min_value=limit, max_value=limit + 10000)
        pagination = self.pagination(offset=offset, limit=limit)
        request = mocker.MagicMock(url_for=mocker.MagicMock(return_value=domain))
        objects = [mocker.MagicMock() for _ in range(1)]
        schema = mocker.MagicMock(spec=BaseModel)
        total = faker.pyint(min_value=limit + 1, max_value=limit + 10000)
        endpoint_name = faker.pystr()

        response = BasePagination.get_paginated_response(
            pagination=pagination,
            request=request,
            objects=objects,
            schema=schema,
            total=total,
            endpoint_name=endpoint_name,
        )

        assert response.objects == [schema.from_orm(obj) for obj in objects]
        assert response.offset == offset
        assert response.limit == limit
        assert response.previous_uri == f"{domain}?offset={offset-limit}&limit={limit}"
        assert response.next_uri == f"{domain}?offset={offset+limit}&limit={limit}"


class TestBaseSorting:
    def test__init__(self, mocker: MockerFixture) -> None:
        model = mocker.MagicMock(spec=Base)
        columns = [mocker.MagicMock(key="field1"), mocker.MagicMock(key="field2")]

        sorting = BaseSorting(model=model, available_columns=columns)

        assert sorting.model == model
        assert sorting.available_columns == columns
        assert sorting.available_columns_names == [col.key for col in columns]

    def test__init__default(self, mocker: MockerFixture) -> None:
        model = mocker.MagicMock(spec=Base)

        sorting = BaseSorting(model=model)

        assert sorting.model == model
        assert sorting.available_columns == []
        assert sorting.available_columns_names == []

    def test__call__(self, faker: Faker, mocker: MockerFixture) -> None:
        build_sorting_mock = mocker.patch.object(target=BaseSorting, attribute="build_sorting")
        sorting = BaseSorting(model=mocker.MagicMock(spec=Base))
        sorting_in = faker.pylist(value_types=[str])

        result = sorting(sorting=sorting_in)

        build_sorting_mock.assert_called_once_with(sorting=sorting_in)
        assert result == build_sorting_mock(sorting=sorting_in)

    def test_build_sorting(self, faker: Faker, mocker: MockerFixture) -> None:
        model = mocker.MagicMock(autospec=True)
        model.included = mocker.MagicMock(key="included")
        model.field2 = mocker.MagicMock(key="field2")
        model.field3 = mocker.MagicMock(key="field3")
        sorting_instance = BaseSorting(model=model, available_columns=[model.included, model.field2, model.field3])
        sorting = ["-included  ", "   field2", "    +field3   ", "not_included1", "-not_included2"]

        result = sorting_instance.build_sorting(sorting=sorting)

        assert result == [model.included.desc(), model.field2.asc(), model.field3.asc()]

    def test_build_sorting_default(self, faker: Faker, mocker: MockerFixture) -> None:
        model = mocker.MagicMock(autospec=True)
        model.created_at = mocker.MagicMock(key="created_at")
        sorting_instance = BaseSorting(model=model, available_columns=[model.created_at])

        result = sorting_instance.build_sorting(sorting=None)  # no sorting at all

        # produces `-created_at` if it inside `available_columns` and exists at `Model(Base)` level
        assert result == [model.created_at.desc()]


async def test_get_async_session(mocker: MockerFixture) -> None:
    async_session_factory_mock = mocker.patch(
        target="apps.CORE.dependencies.async_session_factory", return_value=mocker.MagicMock()
    )
    async_gen_session = get_async_session()

    result = [i async for i in async_gen_session]

    assert result[0] == await async_session_factory_mock().__aenter__()


@pytest.mark.debug()
def test_get_session(mocker: MockerFixture) -> None:
    session_factory_mock = mocker.patch(
        target="apps.CORE.dependencies.session_factory",
        return_value=mocker.MagicMock(test=mocker.MagicMock(side_effect=IntegrityError("", "", ""))),
    )
    gen_session = get_session()

    result = next(gen_session)
    result.test()

    print(True)
