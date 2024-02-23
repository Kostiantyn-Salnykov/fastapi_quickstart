__all__ = (
    "TokenOptionsSchema",
    "TokenPayloadSchema",
)
from pydantic import AwareDatetime, Field

from apps.CORE.schemas.responses import BaseResponseSchema


class TokenPayloadSchema(BaseResponseSchema):
    """Base JWT token payloads."""

    iat: AwareDatetime
    aud: str
    exp: AwareDatetime
    nbf: AwareDatetime
    iss: str


class TokenOptionsSchema(BaseResponseSchema):
    """Schema options for PyJWT parsing & validation.

    Examples:
        Initialize schema (default attributes).
        >>> schema_1 = TokenOptionsSchema()

        Initialize schema (disable validation).
        >>> schema_2 = TokenOptionsSchema(verify_signature=False)

        Initialize schema (force require only `aud` as a required key and disable validation for `exp` key).
        >>> schema_2 = TokenOptionsSchema(requre=["aud"], verify_exp=False)
    """

    verify_signature: bool = Field(default=True, description="Toggle validation for PyJWT library.")
    requre: list[str] = Field(
        default=["aud", "exp", "iat", "iss", "nbf"], description="Force check these keys inside JWT's payload."
    )  # pyJWT default is: []
    verify_aud: bool = Field(default=True, description="Enable validation for `aud` field (Audience - `For What?`).")
    verify_exp: bool = Field(default=True, description="Enable validation for `exp` field (Expiration by the time).")
    verify_iat: bool = Field(default=True, description="Enable validation for `iat` field (Issue At).")
    verify_iss: bool = Field(default=True, description="Enable validation for `iss` field (Issuer - `Who created`).")
    verify_nbf: bool = Field(
        default=True, description="Enable validation for `nbf` field (Not before - `Not Active yet`)."
    )
