__all__ = (
    "PasswordsManager",
    "TokensManager",
)

import datetime
import secrets
from collections.abc import Sequence

import bcrypt
import jwt
from pydantic import BaseModel

from apps.CORE.enums import TokenAudience
from apps.CORE.exceptions import BackendError
from apps.CORE.helpers import utc_now
from apps.CORE.schemas import TokenOptionsSchema
from apps.CORE.types import DatetimeOrNone
from settings import Settings


class PasswordsManager:
    @staticmethod
    def make_password(*, password: str) -> str:
        """Hashing string password value and returns password hash.

        Args:
            password (str): Password raw value.

        Returns:
            - (str): Hashed password value.

        Examples:
            >>> pm = PasswordsManager()
            >>> pm.make_password(password="SuperSecurePassword")
            '$2b$12$z9Vb9dw7jz/X9RrU4fLAMuFzzYv1e5Y5T/EvQmdA6gruZ3DUUEJR2'
        """
        return bcrypt.hashpw(password=password.encode(encoding="utf-8"), salt=bcrypt.gensalt()).decode(encoding="utf-8")

    @staticmethod
    def check_password(*, password: str, password_hash: str) -> bool:
        """Check password and password hash then returns boolean result.

        Args:
            password (str): Raw password to check.
            password_hash (str): Password hash to check on password.

        Returns:
            - (bool): Result of successfully, where True => Success and False => Failed.

        Examples:
            >>> pm = PasswordsManager()
            >>> password = "SuperSecurePassword"
            >>> password_hash = pm.make_password(password=password)
            >>> pm.check_password(password=password, password_hash=password_hash)
            True
            >>> pm.check_password(password="NotSecurePassword", password_hash=password_hash)
            False
        """
        return bcrypt.checkpw(
            password=password.encode(encoding="utf-8"), hashed_password=password_hash.encode(encoding="utf-8")
        )

    @staticmethod
    def generate_password(*, length: int = 8) -> str:
        """Randomly generates password specified length.

        Args:
            length (int): Number of generated characters for password.

        Returns:
            - (str): Randomly generated raw password.

        Examples:
            >>> pm = PasswordsManager()
            >>> pm.generate_password()
            "5Zak_iX3QkY"
            >>> pm.generate_password(length=10)
            "yd8vl5dzWR0o0g"
        """
        return secrets.token_urlsafe(nbytes=length)


class TokensManager:
    def __init__(
        self,
        *,
        secret_key: str = Settings.TOKENS_SECRET_KEY,
        algorithm: str = "HS256",
        default_token_lifetime: datetime.timedelta = datetime.timedelta(minutes=30),
    ) -> None:
        """Initializer for TokensManager.

        Attributes:
            secret_key (str): Securely stored key for encoding and decoding tokens.
            algorithm (str): Encoding algorythm (default HS256).
            default_token_lifetime (datetime.timedelta):  Setting for `exp` parameter of JWT (in instance level).

        Examples:
            Manual usage:
            >>> from apps.CORE.managers import TokensManager
            >>> tm = TokensManager()  # construct & initialize with default parameters
            >>> code = tm.create_code(data={"key": "value", "key2": True, "key3": 123})
            >>> tm.read_code(code=code)
            {"key": "value", "key2": True, "key3": 123, "iat": 1660655886, "aud": "access", "exp": 1660657686,
            "nbf": 1660655886, "iss": ""}

            Or it posible to use inside FastAPI instance:
            >>> from apps.CORE.managers import TokensManager
            >>> from fastapi import FastAPI
            >>> app = FastAPI()
            # construct & initialize with default parameters for FastAPI instance `state`
            >>> app.state.tokens_manager = TokensManager()

            Then is will be available inside routers from `request.app.state.tokens_manager`, where `request` is a
            `fastapi.Request`
        """
        self._secret_key = secret_key
        self._algorithm = algorithm
        self.default_token_lifetime = default_token_lifetime

    def create_code(
        self,
        *,
        data: dict[str, str | int | float | dict | list | bool] | None = None,
        aud: TokenAudience = TokenAudience.ACCESS,  # Audience
        iat: DatetimeOrNone = None,  # Issued at datetime
        exp: DatetimeOrNone = None,  # Expired at datetime
        nbf: DatetimeOrNone = None,  # Not before datetime
        iss: str = Settings.TOKENS_ISSUER,  # Issuer
    ) -> str:
        """Method for generation of JWT token.

        Args:
            data (dict[str, str | int | float | dict | list | bool] | None): Data that should be encoded in JWT token.
            aud (TokenAudience): Audience `aud` parameter of JWT (For what?)
            iat (datetime.datetime): Issued At `iat` parameter of JWT (When created?)
            exp (datetime.datetime): Expire At `exp` parameter of JWT (When expires?)
            nbf (datetime.datetime): Not Valid Before `nbf` parameter of JWT (From what period?)
            iss (str): Issuer `iss` parameter of JWT (Who generates token?)

        Returns:
            - (str): JWT code

        Examples:
            >>> tm = TokensManager()
            >>> tm.create_code(data={"key": "value"})
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJrZXkiOiJ2YWx1ZSIsImlhdCI6MTY2MDY1NzEwMSwiYXVkIjoiYWNjZXNzIiwiZXhwIj
            oxNjYwNjU4OTAxLCJuYmYiOjE2NjA2NTcxMDEsImlzcyI6IiJ9.qKT7VZVAcK2viU-jFLD44PRsh6-pB1rCVkPFKozTtJs"
        """
        if data is None:
            data = {}
        now = utc_now()
        if iat is None:
            iat = now
        if exp is None:
            exp = now + self.default_token_lifetime
        if nbf is None:
            nbf = now
        payload = data.copy()
        payload |= {"iat": iat, "aud": aud.value, "exp": exp, "nbf": nbf, "iss": iss}
        return jwt.encode(payload=payload, key=self._secret_key, algorithm=self._algorithm)

    def read_code(
        self,
        *,
        code: str,
        aud: TokenAudience | Sequence[TokenAudience] = TokenAudience.ACCESS,  # Audience
        iss: str = Settings.TOKENS_ISSUER,  # Issuer
        leeway: int = 0,  # provide extra time in seconds to validate (iat, exp, nbf)
        convert_to: type[BaseModel] | None = None,
        options: TokenOptionsSchema | None = None,
    ) -> BaseModel | dict[str, str | int | float | dict | list | bool]:
        """Method for parse and validate JWT token.

        Args:
            code (str): JWT token to parse & validate.
            aud (TokenAudience | Sequence[TokenAudience]): Audience `aud` to check with. You can check across multiple
                audiences.
            iss (str): Issuer `iss` of token.
            leeway (int): Extra seconds for validate token, applies to `iat`, `exp`, `nbf`.
            convert_to (Type[BaseModel]): You can provide Schema that you need after parsing a token. It should be
                based on `Pydantic.BaseModel`.
            options (TokenOptionsSchema): Extra options for PyJWT parsing & validation.

        Raises:
            ManagerException: In case of validation errors.
            TokenExpired: In case of `exp` validation error.
            InvalidToken: In case of invalid token signature.

        Returns:
            dict[str, str | int | float | dict | list | bool]: Payload with python's dict format.
            BaseModel: `Pydantic.BaseModel` instance from `convert_to` keyword argument.

        Examples:
            >>> tm = TokensManager()
            >>> code: str = "JWT TOKEN HERE"
            >>> payload: dict = tm.read_code(code=code)
        """
        try:
            options = options or TokenOptionsSchema()
            audience = [item.value for item in aud] if isinstance(aud, set | list | tuple) else aud.value
            payload: dict[str, str | int | float | dict | list | bool] = jwt.decode(
                jwt=code,
                key=self._secret_key,
                algorithms=[self._algorithm],
                leeway=leeway,
                audience=audience,
                issuer=iss,
                options=options.dict(),
            )
            if convert_to:
                payload = convert_to(**payload)
        except jwt.exceptions.InvalidIssuerError as error:
            raise BackendError(message="Invalid JWT issuer.") from error
        except jwt.exceptions.InvalidAudienceError as error:
            raise BackendError(message="Invalid JWT audience.") from error
        except jwt.exceptions.ExpiredSignatureError as error:
            raise BackendError(message="Expired JWT token.") from error
        except jwt.exceptions.ImmatureSignatureError as error:
            raise BackendError(message="The token is not valid yet.") from error
        # base error exception from pyjwt
        except jwt.exceptions.PyJWTError as error:
            raise BackendError(message="Invalid JWT.") from error
        else:
            return payload
