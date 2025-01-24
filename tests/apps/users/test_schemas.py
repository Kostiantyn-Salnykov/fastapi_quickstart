import pytest

from src.api.users.schemas.requests import UserUpdateSchema


class TestUserUpdateSchema:
    def test_validate_passwords_success(self) -> None:
        data = {"new_password": "12345678", "old_password": "12345678"}

        result_old = UserUpdateSchema(**data).model_dump(exclude_unset=True)
        assert result_old == data

        result_new = UserUpdateSchema(**data).model_dump(exclude_unset=True)
        assert result_new == data

    def test_validate_new_password_error(self) -> None:
        data = {"new_password": "12345678"}

        with pytest.raises(ValueError, match="You should provide old password to set up new one."):
            UserUpdateSchema(**data)

    def test_validate_old_password_error(self) -> None:
        data = {"old_password": "12345678"}

        with pytest.raises(ValueError, match="It makes no sense to send the old password without sending the new one."):
            UserUpdateSchema(**data)
