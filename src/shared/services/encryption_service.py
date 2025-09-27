"""
Encryption Service for sensitive data storage

Provides symmetric encryption for sensitive data like refresh tokens
before storing them in the database.
"""
import os
import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting/decrypting sensitive data"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize with encryption key"""
        self._fernet = None
        if encryption_key:
            self._setup_fernet(encryption_key)
    
    def _setup_fernet(self, encryption_key: str) -> None:
        """Setup Fernet encryption with the provided key"""
        try:
            # Use the key directly if it's already base64 encoded Fernet key
            if len(encryption_key) == 44 and encryption_key.endswith('='):
                key = encryption_key.encode()
            else:
                # Derive a Fernet key from the provided encryption key
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b'carwash_salt_2024',  # Static salt for consistency
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
            
            self._fernet = Fernet(key)
            logger.info("Encryption service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption service: {e}")
            raise ValueError("Failed to initialize encryption service")
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        if not self._fernet:
            raise ValueError("Encryption service not initialized")
        
        try:
            encrypted_data = self._fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError("Encryption failed")
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        if not self._fernet:
            raise ValueError("Encryption service not initialized")
        
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self._fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Decryption failed")
    
    def encrypt_list(self, data_list: list) -> list:
        """Encrypt a list of strings"""
        return [self.encrypt(item) for item in data_list if item]
    
    def decrypt_list(self, encrypted_list: list) -> list:
        """Decrypt a list of encrypted strings"""
        decrypted = []
        for item in encrypted_list:
            try:
                decrypted.append(self.decrypt(item))
            except ValueError:
                # Skip invalid encrypted data
                logger.warning("Skipping invalid encrypted token")
                continue
        return decrypted
    
    @classmethod
    def generate_key(cls) -> str:
        """Generate a new Fernet encryption key"""
        return Fernet.generate_key().decode()


# Global encryption service instance
_encryption_service: Optional[EncryptionService] = None


def init_encryption_service(encryption_key: Optional[str] = None) -> EncryptionService:
    """Initialize global encryption service"""
    global _encryption_service
    
    if not encryption_key:
        # Try to get from environment
        encryption_key = os.getenv("ENCRYPTION_KEY") or os.getenv("AUTH_ENCRYPTION_KEY")
    
    if not encryption_key:
        logger.warning("No encryption key provided - encryption service disabled")
        _encryption_service = None
        return None
    
    _encryption_service = EncryptionService(encryption_key)
    return _encryption_service


def get_encryption_service() -> Optional[EncryptionService]:
    """Get global encryption service instance"""
    return _encryption_service


def encrypt_if_available(data: str) -> str:
    """Encrypt data if encryption service is available, otherwise return as-is"""
    if _encryption_service:
        return _encryption_service.encrypt(data)
    return data


def decrypt_if_available(encrypted_data: str) -> str:
    """Decrypt data if encryption service is available, otherwise return as-is"""
    if _encryption_service:
        try:
            return _encryption_service.decrypt(encrypted_data)
        except ValueError:
            # Return as-is if decryption fails (might be unencrypted data)
            return encrypted_data
    return encrypted_data


def encrypt_list_if_available(data_list: list) -> list:
    """Encrypt list if encryption service is available"""
    if _encryption_service:
        return _encryption_service.encrypt_list(data_list)
    return data_list


def decrypt_list_if_available(encrypted_list: list) -> list:
    """Decrypt list if encryption service is available"""
    if _encryption_service:
        return _encryption_service.decrypt_list(encrypted_list)
    return encrypted_list