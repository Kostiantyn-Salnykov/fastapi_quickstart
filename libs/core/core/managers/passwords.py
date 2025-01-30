import secrets

import bcrypt


class PasswordsManager:
    """Manager that working with passwords."""

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
