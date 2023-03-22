"""Utils with Enums."""
import enum


class JSENDStatus(str, enum.Enum):
    """Enum based class to set type of JSEND statuses."""

    SUCCESS = "success"  # 2** and 3** codes
    FAIL = "fail"  # 4** codes
    ERROR = "error"  # 5** codes OR custom Back-end codes.


class TokenAudience(str, enum.Enum):
    """Enum based class to set type of JWT token."""

    ACCESS = "access"
    REFRESH = "refresh"
    # For example extra:
    # CONFIRMATION = "confirmation"
    # RESET_PASSWORD = "reset_password"
    # DELETE_ACCOUNT = "delete_account"


class FOps(str, enum.Enum):
    """Enum for Filter Operations (FOps)."""

    # Operations
    EQUAL = "="
    NOT_EQUAL = "!="
    GREATER = ">"
    LESS = "<"
    GREATER_OR_EQUAL = ">="
    LESS_OR_EQUAL = "<="
    IN = "in"
    NOT_IN = "notin"
    LIKE = "like"
    ILIKE = "ilike"
    STARTSWITH = "startswith"
    ENDSWITH = "endswith"
    ISNULL = "isnull"
    NOT_NULL = "notnull"
    # Aliases
    EQ = EQUAL
    NE = NOT_EQUAL
    G = GREATER
    GE = GREATER_OR_EQUAL
    L = LESS
    LE = LESS_OR_EQUAL


class RatePeriod(str, enum.Enum):
    """Predefined periods for RateLimiters. Used in datetime.timedelta constructor."""

    SECOND = "seconds"
    MINUTE = "minutes"
    HOUR = "hours"
    DAY = "days"
    WEEK = "weeks"
