"""Utils with Enums."""
import enum


class JSENDStatus(str, enum.Enum):
    """Enum based class to set type of JSEND statuses."""

    SUCCESS = "success"  # 2** and 3** codes
    FAIL = "fail"  # 4** codes
    ERROR = "error"  # 5** codes OR custom Back-end codes.
