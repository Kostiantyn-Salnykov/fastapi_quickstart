import pytest

from apps.users.schemas import UserUpdateSchema


class TestUserUpdateSchema:
    def test_validate_passwords_success(self) -> None:
        data = {"new_password": "12345678", "old_password": "12345678"}

        result_old = UserUpdateSchema.validate_old_password(values=data)
        assert result_old == data

        result_new = UserUpdateSchema.validate_new_password(values=data)
        assert result_new == data

    def test_validate_new_password_error(self) -> None:
        data = {"new_password": "12345678"}

        with pytest.raises(ValueError, match="You should provide old password to set up new one."):
            UserUpdateSchema.validate_new_password(values=data)

    def test_validate_old_password_error(self) -> None:
        data = {"old_password": "12345678"}

        with pytest.raises(ValueError, match="It makes no sense to send the old password without sending the new one."):
            UserUpdateSchema.validate_old_password(values=data)
