from enum import Enum

__all__ = ("WishStatuses", "WishComplexities", "WishPriorities")


class WishStatuses(str, Enum):
    """Enum class that describes "Wish.status"."""

    CREATED = "CREATED"
    IN_PROGRESS = "IN PROGRESS"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"
    OUTDATED = "OUTDATED"


class WishComplexities(str, Enum):
    """Enum class that describes "Wish.complexity"."""

    VERY_EASY = "VERY EASY"
    EASY = "EASY"
    NORMAL = "NORMAL"
    HARD = "HARD"
    VERY_HARD = "VERY HARD"
    EPIC = "EPIC"


class WishPriorities(int, Enum):
    """Enum class that describes "Wish.priority"."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
