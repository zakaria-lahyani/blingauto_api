"""
Auth domain entities
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from src.features.auth.domain.enums import AuthRole
from src.shared.utils.timestamp import utc_now


class AuthUser:
    """Authentication User Entity"""
    
    def __init__(
        self,
        email: str,
        password_hash: str = "",
        first_name: str = "",
        last_name: str = "",
        phone: Optional[str] = None,
        role: AuthRole = AuthRole.CLIENT,
        is_active: bool = True,
        id: Optional[UUID] = None,
        # Email verification
        email_verified: bool = False,
        email_verified_at: Optional[datetime] = None,
        email_verification_token: Optional[str] = None,
        email_verification_expires: Optional[datetime] = None,
        # Password reset
        password_reset_token: Optional[str] = None,
        password_reset_expires: Optional[datetime] = None,
        password_reset_requested_at: Optional[datetime] = None,
        password_changed_at: Optional[datetime] = None,
        # Account lockout
        failed_login_attempts: int = 0,
        locked_until: Optional[datetime] = None,
        lockout_count: int = 0,
        last_failed_login: Optional[datetime] = None,
        # Session management
        last_login: Optional[datetime] = None,
        refresh_tokens: Optional[List[Dict[str, Any]]] = None,
        # Timestamps
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        # Validate business rules
        self._validate_user_data(email, first_name, last_name)
        
        self.id = id or uuid4()
        self.email = email.strip().lower() if email else email
        self.password_hash = password_hash
        self.first_name = first_name.strip() if first_name else first_name
        self.last_name = last_name.strip() if last_name else last_name
        self.phone = phone
        self.role = role
        self.is_active = is_active
        
        # Email verification
        self.email_verified = email_verified
        self.email_verified_at = email_verified_at
        self.email_verification_token = email_verification_token
        self.email_verification_expires = email_verification_expires
        
        # Password reset
        self.password_reset_token = password_reset_token
        self.password_reset_expires = password_reset_expires
        self.password_reset_requested_at = password_reset_requested_at
        self.password_changed_at = password_changed_at
        
        # Account lockout
        self.failed_login_attempts = failed_login_attempts
        self.locked_until = locked_until
        self.lockout_count = lockout_count
        self.last_failed_login = last_failed_login
        
        # Session management
        self.last_login = last_login
        self.refresh_tokens = refresh_tokens or []
        
        # Timestamps
        self.created_at = created_at or utc_now()
        self.updated_at = updated_at or utc_now()
    
    def _validate_user_data(self, email: str, first_name: str, last_name: str) -> None:
        """Validate user data business rules"""
        if not email or not email.strip():
            raise ValueError("Email is required")
        if len(email) > 255:
            raise ValueError("Email cannot exceed 255 characters")
        if "@" not in email:
            raise ValueError("Email must be a valid email address")
        
        if not first_name or not first_name.strip():
            raise ValueError("First name is required")
        if len(first_name) > 100:
            raise ValueError("First name cannot exceed 100 characters")
        
        if not last_name or not last_name.strip():
            raise ValueError("Last name is required")
        if len(last_name) > 100:
            raise ValueError("Last name cannot exceed 100 characters")
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        from src.features.auth.infrastructure.security.password_hasher import verify_password
        return verify_password(password, self.password_hash)
    
    def change_password(self, new_password: str):
        """Change user password"""
        from src.features.auth.infrastructure.security.password_hasher import hash_password
        self.password_hash = hash_password(new_password)
        self.password_changed_at = utc_now()
        self.updated_at = utc_now()
    
    def change_role(self, new_role: AuthRole):
        """Change user role"""
        self.role = new_role
        self.updated_at = utc_now()
    
    def verify_email(self):
        """Mark email as verified"""
        self.email_verified = True
        self.email_verified_at = utc_now()
        self.email_verification_token = None
        self.email_verification_expires = None
        self.updated_at = utc_now()
    
    def set_email_verification_token(self, token: str, expires_at: datetime):
        """Set email verification token"""
        self.email_verification_token = token
        self.email_verification_expires = expires_at
        self.updated_at = utc_now()
    
    def set_password_reset_token(self, token: str, expires_at: datetime):
        """Set password reset token"""
        self.password_reset_token = token
        self.password_reset_expires = expires_at
        self.password_reset_requested_at = utc_now()
        self.updated_at = utc_now()
    
    def clear_password_reset_token(self):
        """Clear password reset token"""
        self.password_reset_token = None
        self.password_reset_expires = None
        self.password_reset_requested_at = None
        self.updated_at = utc_now()
    
    def record_failed_login(self):
        """Record failed login attempt"""
        self.failed_login_attempts += 1
        self.last_failed_login = utc_now()
        self.updated_at = utc_now()
    
    def lock_account(self, until: datetime):
        """Lock user account"""
        self.locked_until = until
        self.lockout_count += 1
        self.updated_at = utc_now()
    
    def unlock_account(self):
        """Unlock user account"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.lockout_count = 0
        self.updated_at = utc_now()
    
    def record_successful_login(self):
        """Record successful login"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login = utc_now()
        self.updated_at = utc_now()
    
    def add_refresh_token(self, token_info: Dict[str, Any]):
        """Add refresh token to user (encrypted before storage)"""
        from src.shared.services.encryption_service import encrypt_if_available
        
        # Encrypt sensitive token data before storing
        encrypted_token_info = token_info.copy()
        if 'token_hash' in encrypted_token_info:
            encrypted_token_info['token_hash'] = encrypt_if_available(encrypted_token_info['token_hash'])
        if 'family_id' in encrypted_token_info:
            encrypted_token_info['family_id'] = encrypt_if_available(encrypted_token_info['family_id'])
        
        self.refresh_tokens.append(encrypted_token_info)
        self.updated_at = utc_now()
    
    def remove_refresh_token(self, token_hash: str):
        """Remove specific refresh token"""
        from src.shared.services.encryption_service import encrypt_if_available, decrypt_if_available
        
        # Encrypt the token hash to match stored format
        encrypted_token_hash = encrypt_if_available(token_hash)
        
        self.refresh_tokens = [
            token for token in self.refresh_tokens
            if decrypt_if_available(token.get('token_hash', '')) != token_hash and 
               token.get('token_hash') != encrypted_token_hash
        ]
        self.updated_at = utc_now()
    
    def clear_all_refresh_tokens(self):
        """Clear all refresh tokens"""
        self.refresh_tokens = []
        self.updated_at = utc_now()
    
    def get_decrypted_refresh_tokens(self) -> List[Dict[str, Any]]:
        """Get refresh tokens with decrypted sensitive data"""
        from src.shared.services.encryption_service import decrypt_if_available
        
        decrypted_tokens = []
        for token in self.refresh_tokens:
            decrypted_token = token.copy()
            if 'token_hash' in decrypted_token:
                decrypted_token['token_hash'] = decrypt_if_available(decrypted_token['token_hash'])
            if 'family_id' in decrypted_token:
                decrypted_token['family_id'] = decrypt_if_available(decrypted_token['family_id'])
            decrypted_tokens.append(decrypted_token)
        
        return decrypted_tokens
    
    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked"""
        if not self.locked_until:
            return False
        return utc_now() < self.locked_until
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = utc_now()