from enum import Enum

__all__ = ("UsersStatuses",)


class UsersStatuses(str, Enum):
    UNCONFIRMED = "UNCONFIRMED"  # default, after registration (can't log in, need to active through email)
    CONFIRMED = "CONFIRMED"  # after confirmation by email (all good state)
    FORCE_CHANGE_PASSWORD = "FORCE_CHANGE_PASSWORD"  # confirmed, but user need to update temporary password
    EXTERNAL_PROVIDER = "EXTERNAL_PROVIDER"  # logged via Google, Meta, etc...
    ARCHIVED = "ARCHIVED"  # deleted user (force randomized email and data)
