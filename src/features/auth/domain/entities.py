"""
Auth domain entities
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from src.features.auth.domain.enums import AuthRole


@dataclass
class AuthUser:
    """Authentication User Entity"""
    
    id: UUID = field(default_factory=uuid4)
    email: str = ""
    password_hash: str = ""
    first_name: str = ""
    last_name: str = ""
    phone: Optional[str] = None
    role: AuthRole = AuthRole.CLIENT
    is_active: bool = True
    
    # Email verification
    email_verified: bool = False
    email_verified_at: Optional[datetime] = None
    email_verification_token: Optional[str] = None
    email_verification_expires: Optional[datetime] = None
    
    # Password reset
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None
    password_reset_requested_at: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    
    # Account lockout
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    lockout_count: int = 0
    last_failed_login: Optional[datetime] = None
    
    # Session management
    last_login: Optional[datetime] = None
    refresh_tokens: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        from ..infrastructure.security.password_hasher import verify_password
        return verify_password(password, self.password_hash)
    
    def change_password(self, new_password: str):
        """Change user password"""
        from ..infrastructure.security.password_hasher import hash_password
        self.password_hash = hash_password(new_password)
        self.password_changed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def change_role(self, new_role: AuthRole):
        """Change user role"""
        self.role = new_role
        self.updated_at = datetime.utcnow()
    
    def verify_email(self):
        """Mark email as verified"""
        self.email_verified = True
        self.email_verified_at = datetime.utcnow()
        self.email_verification_token = None
        self.email_verification_expires = None
        self.updated_at = datetime.utcnow()
    
    def set_email_verification_token(self, token: str, expires_at: datetime):
        """Set email verification token"""
        self.email_verification_token = token
        self.email_verification_expires = expires_at
        self.updated_at = datetime.utcnow()
    
    def set_password_reset_token(self, token: str, expires_at: datetime):
        """Set password reset token"""
        self.password_reset_token = token
        self.password_reset_expires = expires_at
        self.password_reset_requested_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def clear_password_reset_token(self):
        """Clear password reset token"""
        self.password_reset_token = None
        self.password_reset_expires = None
        self.password_reset_requested_at = None
        self.updated_at = datetime.utcnow()
    
    def record_failed_login(self):
        """Record failed login attempt"""
        self.failed_login_attempts += 1
        self.last_failed_login = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def lock_account(self, until: datetime):
        """Lock user account"""
        self.locked_until = until
        self.lockout_count += 1
        self.updated_at = datetime.utcnow()
    
    def unlock_account(self):
        """Unlock user account"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.lockout_count = 0
        self.updated_at = datetime.utcnow()
    
    def record_successful_login(self):
        """Record successful login"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
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
        self.updated_at = datetime.utcnow()
    
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
        self.updated_at = datetime.utcnow()
    
    def clear_all_refresh_tokens(self):
        """Clear all refresh tokens"""
        self.refresh_tokens = []
        self.updated_at = datetime.utcnow()
    
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
        return datetime.utcnow() < self.locked_until
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.utcnow()