import enum


class PermissionActions(str, enum.Enum):
    """Enum based class to set type of action for permissions."""

    CREATE = "create"  # POST
    READ = "read"  # GET
    UPDATE = "update"  # PUT / PATCH
    DELETE = "delete"  # DELETE
