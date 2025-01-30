import datetime
from collections.abc import Sequence

import jwt
from pydantic import BaseModel

from core.annotations import DatetimeOrNone
from core.enums import TokenAudience
from core.exceptions import BackendError
from core.helpers import utc_now
from core.managers.schemas import TokenOptionsSchema
from core.managers.settings import managers_settings


class TokensManager:
    """Manager that working with JWT tokens."""

    def __init__(
        self,
        *,
        secret_key: str = managers_settings.TOKENS_SECRET_KEY,
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
            >>> from core.managers.tokens import TokensManager
            >>> tm = TokensManager()  # construct & initialize with default parameters
            >>> code = tm.create_code(data={"key": "value", "key2": True, "key3": 123})
            >>> tm.read_code(code=code)
            {"key": "value", "key2": True, "key3": 123, "iat": 1660655886, "aud": "access", "exp": 1660657686,
            "nbf": 1660655886, "iss": ""}

            Or it posible to use inside FastAPI instance:
            >>> from core.managers.tokens import TokensManager
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
        iss: str = managers_settings.TOKENS_ISSUER,  # Issuer
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
        iss: str = managers_settings.TOKENS_ISSUER,  # Issuer
        leeway: int = 0,  # provide extra time in seconds to validate (iat, exp, nbf)
        response_schema: type[BaseModel] | None = None,
        options: TokenOptionsSchema | None = None,
    ) -> BaseModel | dict[str, str | int | float | dict | list | bool]:
        """Method for parse and validate JWT token.

        Args:
            code (str): JWT token to parse & validate.
            aud (TokenAudience | Sequence[TokenAudience]): Audience `aud` to check with. You can check across multiple
                audiences.
            iss (str): Issuer `iss` of token.
            leeway (int): Extra seconds for validate token, applies to `iat`, `exp`, `nbf`.
            response_schema (Type[BaseModel]): You can provide Schema that you need after parsing a token. It should be
                based on `Pydantic.BaseModel`.
            options (TokenOptionsSchema): Extra options for PyJWT parsing & validation.

        Raises:
            ManagerException: In case of validation errors.
            TokenExpired: In case of `exp` validation error.
            InvalidToken: In case of invalid token signature.

        Returns:
            dict[str, str | int | float | dict | list | bool]: Payload with python's dict format.
            BaseModel: `Pydantic.BaseModel` instance from `response_schema` keyword argument.

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
                options=options.model_dump(),
            )
            if response_schema:
                payload = response_schema(**payload)
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
