import datetime

import pytest
from faker import Faker

from apps.CORE.enums import TokenAudience
from apps.CORE.exceptions import BackendError
from apps.CORE.helpers import utc_now
from apps.CORE.managers import PasswordsManager, TokensManager
from apps.CORE.schemas import TokenOptionsSchema, TokenPayloadSchema


class TestPasswordsManager:
    @classmethod
    def setup_class(cls) -> None:
        cls.passwords_manager = PasswordsManager()

    def test_manager(self, faker: Faker) -> None:
        password_length = faker.pyint(min_value=8, max_value=32)
        password = self.passwords_manager.generate_password(length=password_length)

        password_hash = self.passwords_manager.make_password(password=password)

        assert self.passwords_manager.check_password(password=password, password_hash=password_hash) is True
        assert self.passwords_manager.check_password(password="fail", password_hash=password_hash) is False


class TestTokensManager:
    @classmethod
    def setup_class(cls) -> None:
        cls.tokens_manager = TokensManager()
        cls.default_keys = {"iat", "exp", "nbf", "aud", "iss"}

    def test_create_read_success(self, faker: Faker) -> None:
        data_key = faker.pystr()
        data = {data_key: faker.pystr()}
        token = self.tokens_manager.create_code(data=data)

        payload = self.tokens_manager.read_code(code=token)

        assert payload[data_key] == data[data_key]
        assert self.default_keys.issubset(payload.keys())

    def test_iss_error(self, faker: Faker) -> None:
        iss = faker.pystr()
        token = self.tokens_manager.create_code(iss=iss)

        with pytest.raises(BackendError) as exception_context:
            self.tokens_manager.read_code(code=token)

        assert isinstance(exception_context.value, BackendError)
        assert exception_context.value.message == "Invalid JWT issuer."

    def test_aud_error(self, faker: Faker) -> None:
        aud = TokenAudience.REFRESH
        token = self.tokens_manager.create_code(aud=aud)

        with pytest.raises(BackendError) as exception_context:
            self.tokens_manager.read_code(code=token)

        assert isinstance(exception_context.value, BackendError)
        assert exception_context.value.message == "Invalid JWT audience."

    def test_exp_error(self, faker: Faker) -> None:
        exp = utc_now() - datetime.timedelta(minutes=30)
        token = self.tokens_manager.create_code(exp=exp)

        with pytest.raises(BackendError) as exception_context:
            self.tokens_manager.read_code(code=token)

        assert isinstance(exception_context.value, BackendError)
        assert exception_context.value.message == "Expired JWT token."

    def test_nbf_error(self, faker: Faker) -> None:
        nbf = utc_now() + datetime.timedelta(minutes=1)
        token = self.tokens_manager.create_code(nbf=nbf)

        with pytest.raises(BackendError) as exception_context:
            self.tokens_manager.read_code(code=token)

        assert isinstance(exception_context.value, BackendError)
        assert exception_context.value.message == "The token is not valid yet."

    def test_iat_error(self, faker: Faker) -> None:
        iat = utc_now() + datetime.timedelta(minutes=1)
        token = self.tokens_manager.create_code(iat=iat)

        with pytest.raises(BackendError) as exception_context:
            self.tokens_manager.read_code(code=token)

        assert isinstance(exception_context.value, BackendError)
        assert exception_context.value.message == "The token is not valid yet."

    def test_invalid_error(self, faker: Faker) -> None:
        token = TokensManager(secret_key="test").create_code()

        with pytest.raises(BackendError) as exception_context:
            self.tokens_manager.read_code(code=token)

        assert isinstance(exception_context.value, BackendError)
        assert exception_context.value.message == "Invalid JWT."

    def test_convert_to_success(self, faker: Faker) -> None:
        class Schema(TokenPayloadSchema):
            something: str

        data_key = "something"
        data = {data_key: faker.pystr()}
        token = self.tokens_manager.create_code(data=data)

        payload_schema = self.tokens_manager.read_code(code=token, convert_to=Schema)

        assert isinstance(payload_schema, Schema)
        assert payload_schema.something == data[data_key]
        payload = payload_schema.dict()
        assert payload[data_key] == data[data_key]
        assert self.default_keys.issubset(payload.keys())

    def test_multiple_audiences_success(self, faker: Faker) -> None:
        data_key = "something"
        data = {data_key: faker.pystr()}
        token = self.tokens_manager.create_code(data=data)

        payload = self.tokens_manager.read_code(code=token, aud=(TokenAudience.ACCESS, TokenAudience.REFRESH))

        assert payload[data_key] == data[data_key]
        assert self.default_keys.issubset(payload.keys())

    def test_options_success(self) -> None:
        exp = utc_now()
        token = self.tokens_manager.create_code(data={}, exp=exp)

        payload = self.tokens_manager.read_code(code=token, options=TokenOptionsSchema(verify_exp=False))

        assert self.default_keys.issubset(payload.keys())
