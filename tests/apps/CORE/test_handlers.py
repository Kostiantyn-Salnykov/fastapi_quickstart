import pytest
from faker import Faker
from fastapi import status
from pytest_mock import MockerFixture

from apps.CORE.enums import JSENDStatus
from apps.CORE.exceptions import BackendError
from apps.CORE.handlers import backend_exception_handler, integrity_error_handler, validation_exception_handler
from settings import Settings


def test_backend_exception_handler(faker: Faker, mocker: MockerFixture) -> None:
    exception = BackendError(message=faker.pystr())
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


class TestIntegrityErrorHandler:
    def test_integrity_error_handler_duplicate(self, faker: Faker, mocker: MockerFixture, monkeypatch) -> None:
        monkeypatch.setattr(target=Settings, name="DEBUG", value=False)
        exception_mock = mocker.MagicMock()
        exception_mock.args = ["duplicate"]

        with pytest.raises(BackendError) as exception_context:
            integrity_error_handler(error=exception_mock)

        assert str(exception_context.value) == str(
            BackendError(message="Conflict error.", status=status.HTTP_409_CONFLICT)
        )

    def test_integrity_error_handler_duplicate_debug(self, faker: Faker, mocker: MockerFixture, monkeypatch) -> None:
        monkeypatch.setattr(target=Settings, name="DEBUG", value=True)
        exception_mock = mocker.MagicMock()
        exception_mock.args = ["duplicate"]
        expected_message = faker.pystr()
        exception_mock.orig.args = [f"1\n2\n{expected_message}"]

        with pytest.raises(BackendError) as exception_context:
            integrity_error_handler(error=exception_mock)

        assert str(exception_context.value) == str(
            BackendError(message=expected_message, status=status.HTTP_409_CONFLICT)
        )

    def test_integrity_error_handler_other(self, faker: Faker, mocker: MockerFixture, monkeypatch) -> None:
        monkeypatch.setattr(target=Settings, name="DEBUG", value=False)
        exception_mock = mocker.MagicMock()
        exception_mock.args = ["something"]

        with pytest.raises(BackendError) as exception_context:
            integrity_error_handler(error=exception_mock)

        assert str(exception_context.value) == str(
            BackendError(
                status=JSENDStatus.ERROR, message="Internal server error.", code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        )

    def test_integrity_error_handler_other_debug(self, faker: Faker, mocker: MockerFixture, monkeypatch) -> None:
        monkeypatch.setattr(target=Settings, name="DEBUG", value=True)
        exception_mock = mocker.MagicMock()
        expected_response = faker.pystr()
        exception_mock.__str__.return_value = expected_response
        exception_mock.args = ["something"]

        with pytest.raises(BackendError) as exception_context:
            integrity_error_handler(error=exception_mock)

        assert str(exception_context.value) == str(
            BackendError(
                status=JSENDStatus.ERROR, message=expected_response, code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        )
