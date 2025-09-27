"""
JWT token handling
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from jose import JWTError, jwt
import secrets

from src.features.auth.config import AuthConfig


class JWTHandler:
    """Handle JWT token creation and verification"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
    
    def create_access_token(
        self, 
        user_id: str, 
        email: str, 
        role: str,
        expires_minutes: Optional[int] = None
    ) -> str:
        """Create access token"""
        if expires_minutes is None:
            expires_minutes = self.config.access_token_expire_minutes
        
        expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
        
        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "type": "access",
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(
            payload, 
            self.config.jwt_secret_key, 
            algorithm=self.config.jwt_algorithm
        )
    
    def create_refresh_token(
        self, 
        user_id: str,
        family_id: Optional[str] = None,
        expires_days: Optional[int] = None
    ) -> str:
        """Create refresh token"""
        if expires_days is None:
            expires_days = self.config.refresh_token_expire_days
        
        if family_id is None:
            family_id = secrets.token_urlsafe(16)
        
        expire = datetime.utcnow() + timedelta(days=expires_days)
        
        payload = {
            "sub": user_id,
            "type": "refresh", 
            "family_id": family_id,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(
            payload,
            self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm
        )
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode token"""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm]
            )
            return payload
        except JWTError:
            return None
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode token without verification (for expired tokens)"""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
                options={"verify_exp": False}
            )
            return payload
        except JWTError:
            return None
    
    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired"""
        payload = self.decode_token(token)
        if not payload:
            return True
        
        exp = payload.get("exp")
        if not exp:
            return True
        
        return datetime.fromtimestamp(exp) < datetime.utcnow()
    
    def get_token_user_id(self, token: str) -> Optional[str]:
        """Extract user ID from token"""
        payload = self.decode_token(token)
        if payload:
            return payload.get("sub")
        return None