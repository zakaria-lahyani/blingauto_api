from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordHasher:
    """Password hashing and verification utilities."""

    @staticmethod
    def hash(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def needs_rehash(hashed_password: str) -> bool:
        """Check if password hash needs to be updated."""
        return pwd_context.needs_update(hashed_password)


password_hasher = PasswordHasher()