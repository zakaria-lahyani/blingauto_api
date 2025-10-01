from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import DecodeError, InvalidTokenError

from app.core.config import settings


class JWTHandler:
    """JWT token handling utilities."""

    @staticmethod
    def create_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a JWT token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm,
        )
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm],
            )
            return payload
        except (DecodeError, InvalidTokenError):
            return None

    @staticmethod
    def create_access_token(user_id: str, role: str) -> str:
        """Create an access token."""
        data = {
            "sub": user_id,
            "role": role,
            "type": "access",
        }
        expires = timedelta(minutes=settings.access_token_expire_minutes)
        return JWTHandler.create_token(data, expires)

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create a refresh token."""
        data = {
            "sub": user_id,
            "type": "refresh",
        }
        expires = timedelta(days=settings.refresh_token_expire_days)
        return JWTHandler.create_token(data, expires)

    @staticmethod
    def validate_access_token(token: str) -> Optional[Dict[str, Any]]:
        """Validate an access token."""
        payload = JWTHandler.decode_token(token)
        if payload and payload.get("type") == "access":
            return payload
        return None

    @staticmethod
    def validate_refresh_token(token: str) -> Optional[Dict[str, Any]]:
        """Validate a refresh token."""
        payload = JWTHandler.decode_token(token)
        if payload and payload.get("type") == "refresh":
            return payload
        return None


jwt_handler = JWTHandler()