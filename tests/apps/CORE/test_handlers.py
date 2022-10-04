from faker import Faker
from fastapi import status
from pytest_mock import MockerFixture

from apps.CORE.enums import JSENDStatus
from apps.CORE.exceptions import BackendException
from apps.CORE.handlers import backend_exception_handler, validation_exception_handler


def test_backend_exception_handler(faker: Faker, mocker: MockerFixture) -> None:
    exception = BackendException(message=faker.pystr())
    expected_result = faker.pystr()
    orjson_response_mock = mocker.patch(target="apps.CORE.handlers.ORJSONResponse", return_value=expected_result)

    result = backend_exception_handler(request=mocker.MagicMock(), exc=exception)

    orjson_response_mock.assert_called_once_with(content=exception.dict(), status_code=exception.code)
    assert result == expected_result


def test_validation_exception_handler(faker: Faker, mocker: MockerFixture) -> None:
    exception_mock = mocker.MagicMock()
    exception_mock.errors.return_value = [{"loc": "Something", "msg": "test", "type": "TYPE", "ctx": "CONTEXT"}]
    expected_result = faker.pystr()
    orjson_response_mock = mocker.patch(target="apps.CORE.handlers.ORJSONResponse", return_value=expected_result)

    result = validation_exception_handler(request=mocker.MagicMock(), exc=exception_mock)

    orjson_response_mock.assert_called_once_with(
        content={
            "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "data": [{"location": "Something", "message": "Test.", "type": "TYPE", "context": "CONTEXT"}],
            "message": "Validation error.",
            "status": JSENDStatus.FAIL,
        },
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )
    assert result == expected_result
