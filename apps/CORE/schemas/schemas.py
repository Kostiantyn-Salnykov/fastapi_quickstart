__all__ = (
    "TokenPayloadSchema",
    "TokenOptionsSchema",
)
from pydantic import Field

from apps.CORE.schemas.responses import BaseResponseSchema
from apps.CORE.types import Timestamp


class TokenPayloadSchema(BaseResponseSchema):
    """Base JWT token payloads."""

    iat: Timestamp
    aud: str
    exp: Timestamp
    nbf: Timestamp
    iss: str


class TokenOptionsSchema(BaseResponseSchema):
    """Schema options for PyJWT parsing & validation.

    Attributes:
        verify_signature (bool): Toggle validation for PyJWT library. Defaults: `True`

            `True` --> Enabled,

            `False` --> Disabled.

        require (list[str]): Force check these keys inside JWT's payload.

            Defaults: `["aud", "exp", "iat", "iss", "nbf"]`
        verify_aud (bool): Enable validation for `aud` field. Defaults: `True`
        verify_exp (bool): Enable validation for `exp` field. Defaults: `True`
        verify_iat (bool): Enable validation for `iat` field. Defaults: `True`
        verify_iss (bool): Enable validation for `iss` field. Defaults: `True`
        verify_nbf (bool): Enable validation for `nbf` field. Defaults: `True`
    Examples:
        Initialize schema (default attributes).
        >>> schema_1 = TokenOptionsSchema()

        Initialize schema (disable validation).
        >>> schema_2 = TokenOptionsSchema(verify_signature=False)

        Initialize schema (force require only `aud` as a required key and disable validation for `exp` key).
        >>> schema_2 = TokenOptionsSchema(requre=["aud"], verify_exp=False)
    """

    verify_signature: bool = Field(default=True)
    requre: list[str] = Field(default=["aud", "exp", "iat", "iss", "nbf"])  # pyJWT default is: []
    verify_aud: bool = Field(default=True)
    verify_exp: bool = Field(default=True)
    verify_iat: bool = Field(default=True)
    verify_iss: bool = Field(default=True)
    verify_nbf: bool = Field(default=True)
