import pytest
from faker import Faker
from pydantic import BaseModel, Field
from pytest_mock import MockerFixture
from sqlalchemy.exc import IntegrityError

from apps.CORE.db import Base
from apps.CORE.deps import get_async_session, get_redis, get_session
from apps.CORE.deps.filters import QueryFilter, get_sqlalchemy_where_operations_mapper
from apps.CORE.deps.pagination import LimitOffsetPagination
from apps.CORE.deps.sorting import BaseSorting
from apps.CORE.enums import FOps
from apps.CORE.exceptions import BackendError
from apps.CORE.schemas.responses import BaseResponseSchema


class TestBasePagination:
    def setup_method(self) -> None:
        self.pagination = LimitOffsetPagination()

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

        assert isinstance(self.pagination, LimitOffsetPagination)
        assert self.pagination == result
        assert self.pagination.offset == offset
        assert self.pagination.limit == limit

    def test_get_paginated_response(self, faker: Faker, mocker: MockerFixture) -> None:
        domain = faker.url()
        limit: int = faker.pyint(min_value=10, max_value=1000)
        offset: int = faker.pyint(min_value=limit, max_value=limit + 10000)
        pagination = self.pagination(offset=offset, limit=limit)
        request = mocker.MagicMock(url_for=mocker.MagicMock(return_value=domain))
        objects = [mocker.MagicMock() for _ in range(1)]
        schema = mocker.MagicMock(spec=BaseModel)
        total = faker.pyint(min_value=limit + 1, max_value=limit + 10000)
        endpoint_name = faker.pystr()

        response = pagination.paginate(
            request=request,
            objects=objects,
            schema=schema,
            total=total,
            endpoint_name=endpoint_name,
        )

        assert response.objects == [schema.from_orm(obj) for obj in objects]
        assert response.offset == offset
        assert response.limit == limit


class TestBaseSorting:
    def test__init__(self, mocker: MockerFixture) -> None:
        model, schema = mocker.MagicMock(spec=Base), mocker.MagicMock(spec=BaseResponseSchema)
        columns = [mocker.MagicMock(key="field1"), mocker.MagicMock(key="field2")]

        sorting = BaseSorting(model=model, available_columns=columns, schema=schema)

        assert sorting.model == model
        assert sorting.available_columns == columns
        assert sorting.available_columns_names == [col.key for col in columns]

    def test__init__default(self, mocker: MockerFixture) -> None:
        model, schema = mocker.MagicMock(spec=Base), mocker.MagicMock(spec=BaseResponseSchema)

        sorting = BaseSorting(model=model, schema=schema)

        assert sorting.model == model
        assert sorting.available_columns == []
        assert sorting.available_columns_names == []

    def test__call__(self, faker: Faker, mocker: MockerFixture) -> None:
        build_sorting_mock = mocker.patch.object(target=BaseSorting, attribute="build_sorting")
        sorting = BaseSorting(model=mocker.MagicMock(spec=Base), schema=mocker.MagicMock(spec=BaseResponseSchema))
        sorting_in = faker.pylist(value_types=[str])

        result = sorting(sorting=sorting_in)

        build_sorting_mock.assert_called_once_with(sorting=sorting_in)
        assert result == build_sorting_mock(sorting=sorting_in)

    def test_build_sorting(self, faker: Faker, mocker: MockerFixture) -> None:
        model, schema = mocker.MagicMock(autospec=True), mocker.MagicMock(autospec=True)
        mocker.patch.object(
            target=BaseSorting,
            attribute="collect_aliases",
            return_value={"included": "included", "field2": "field2", "field3": "field3"},
        )
        model.included = mocker.MagicMock(key="included")
        model.field2 = mocker.MagicMock(key="field2")
        model.field3 = mocker.MagicMock(key="field3")
        sorting_instance = BaseSorting(
            model=model, available_columns=[model.included, model.field2, model.field3], schema=schema
        )
        sorting = ["-included  ", "   field2", "    +field3   ", "not_included1", "-not_included2"]

        result = sorting_instance.build_sorting(sorting=sorting)

        assert result == [model.included.desc(), model.field2.asc(), model.field3.asc()]

    def test_build_sorting_default(self, faker: Faker, mocker: MockerFixture) -> None:
        model, schema = mocker.MagicMock(autospec=True), mocker.MagicMock(autospec=True)
        mocker.patch.object(target=BaseSorting, attribute="collect_aliases", return_value={})
        model.id = mocker.MagicMock(key="id")
        sorting_instance = BaseSorting(model=model, available_columns=[model.id], schema=schema)

        result = sorting_instance.build_sorting(sorting=None)  # no sorting at all

        # produces `-id` if it inside `available_columns` and exists at `Model(Base)` level
        assert result == [model.id.desc()]

    def test_collect_aliases(self, mocker: MockerFixture) -> None:
        class TestSchema(BaseResponseSchema):
            title: str = Field(alias="t")
            f2: str = Field()

        expected_result = {"t": "title"}
        result = BaseSorting(model=mocker.MagicMock(autospec=True), schema=TestSchema).collect_aliases()

        assert result == expected_result


async def test_get_async_session(mocker: MockerFixture) -> None:
    async_session_factory_mock = mocker.patch(
        target="apps.CORE.deps.async_session_factory", return_value=mocker.MagicMock()
    )
    async_gen_session = get_async_session()

    result = [i async for i in async_gen_session]

    assert result[0] == await async_session_factory_mock().__aenter__()


# TODO: write test
@pytest.mark.debug()
def test_get_session(mocker: MockerFixture) -> None:
    mocker.patch(
        target="apps.CORE.deps.session_factory",
        return_value=mocker.MagicMock(test=mocker.MagicMock(side_effect=IntegrityError("", "", ""))),
    )
    gen_session = get_session()

    result = next(gen_session)
    result.test()

    print(True)


async def test_get_redis() -> None:
    redis = await anext(get_redis())
    result = await redis.ping()

    assert result is True


@pytest.mark.parametrize(
    argnames=("filter_operation", "expected_result"),
    argvalues=(
        (FOps.EQ, "__eq__"),
        (FOps.EQUAL, "__eq__"),
        (FOps.NOT_EQUAL, "__ne__"),
        (FOps.NE, "__ne__"),
        (FOps.GREATER, "__gt__"),
        (FOps.G, "__gt__"),
        (FOps.LESS, "__lt__"),
        (FOps.GREATER_OR_EQUAL, "__ge__"),
        (FOps.GE, "__ge__"),
        (FOps.LESS_OR_EQUAL, "__le__"),
        (FOps.LE, "__le__"),
        (FOps.IN, "in_"),
        (FOps.NOT_IN, "not_in"),
        (FOps.LIKE, "like"),
        (FOps.ILIKE, "ilike"),
        (FOps.STARTSWITH, "startswith"),
        (FOps.ENDSWITH, "endswith"),
        (FOps.ISNULL, "isnull"),
        (FOps.NOT_NULL, "notnull"),
    ),
)
def test_get_sqlalchemy_where_operations_mapper(filter_operation: FOps, expected_result: str) -> None:
    result = get_sqlalchemy_where_operations_mapper(operation_type=filter_operation)

    assert result == expected_result


class TestQueryFilter:
    @pytest.mark.parametrize(argnames="filter_operation", argvalues=(FOps.ISNULL, FOps.NOT_NULL))
    def test_validate_obj_none_result(self, filter_operation: FOps) -> None:
        schema = QueryFilter[str]

        result = schema(field="test", operation=filter_operation, value="test")

        assert result.value is None

    @pytest.mark.parametrize(argnames="filter_operation", argvalues=(FOps.IN, FOps.NOT_IN))
    def test_validate_obj_exception(self, filter_operation: FOps) -> None:
        schema = QueryFilter[str]  # not true generic schema.

        with pytest.raises(BackendError) as exception_context:
            schema(field="test", operation=filter_operation, value="test")

        assert str(exception_context.value) == str(
            BackendError(
                message=f"Filters error. For operation '{filter_operation.value}', the value must be a list (Array[])."
            )
        )

    @pytest.mark.parametrize(argnames="filter_operation", argvalues=(FOps.IN, FOps.NOT_IN))
    def test_validate_obj_success(self, filter_operation: FOps) -> None:
        value = ["test", "test2"]
        schema = QueryFilter[list[str]]

        result = schema(field="test", operation=filter_operation, value=value)

        assert result.value == value

    def test_validate_obj_simple_success(self) -> None:
        value = "test"
        schema = QueryFilter[str]

        result = schema(field="test", operation=FOps.EQ, value=value)

        assert result.value == value
