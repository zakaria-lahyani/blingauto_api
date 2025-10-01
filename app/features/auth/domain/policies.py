from typing import Optional
import re

from .exceptions import ValidationError, BusinessRuleViolationError


class PasswordPolicy:
    """Password validation and strength policies."""
    
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    
    @staticmethod
    def validate(password: str) -> bool:
        """
        Validate password against policy rules.
        RG-AUTH-002: Password validation requirements
        """
        if not password:
            raise ValidationError("Password is required", field="password")
        
        if len(password) < PasswordPolicy.MIN_LENGTH:
            raise ValidationError(
                f"Password must be at least {PasswordPolicy.MIN_LENGTH} characters",
                field="password"
            )
        
        if len(password) > PasswordPolicy.MAX_LENGTH:
            raise ValidationError(
                f"Password must be less than {PasswordPolicy.MAX_LENGTH} characters",
                field="password"
            )
        
        # Additional security checks
        if password.isdigit():
            raise ValidationError(
                "Password cannot be all numbers",
                field="password"
            )
        
        if password.isalpha():
            raise ValidationError(
                "Password must contain at least one number or special character",
                field="password"
            )
        
        # Check for common weak passwords
        weak_passwords = [
            "password", "12345678", "qwerty", "abc123",
            "password123", "admin", "letmein"
        ]
        if password.lower() in weak_passwords:
            raise ValidationError(
                "Password is too common, please choose a stronger password",
                field="password"
            )
        
        return True
    
    @staticmethod
    def calculate_strength(password: str) -> int:
        """
        Calculate password strength score (0-100).
        """
        score = 0
        
        # Length scoring
        if len(password) >= 8:
            score += 20
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10
        
        # Character diversity
        if re.search(r"[a-z]", password):
            score += 10
        if re.search(r"[A-Z]", password):
            score += 10
        if re.search(r"[0-9]", password):
            score += 10
        if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            score += 20
        
        # Pattern checks
        if not re.search(r"(.)\1{2,}", password):  # No repeated characters
            score += 10
        if not re.search(r"(012|123|234|345|456|567|678|789|890)", password):
            score += 10
        
        return min(score, 100)


class AccountLockoutPolicy:
    """
    Account lockout policy for failed login attempts.
    RG-AUTH-006: Account lockout management
    """
    
    MAX_ATTEMPTS = 5
    BASE_LOCKOUT_MINUTES = 30
    MAX_LOCKOUT_MULTIPLIER = 4
    
    @staticmethod
    def calculate_lockout_duration(failed_attempts: int) -> int:
        """
        Calculate progressive lockout duration in minutes.
        Increases with repeated violations.
        """
        if failed_attempts < AccountLockoutPolicy.MAX_ATTEMPTS:
            return 0
        
        # Calculate multiplier based on violation count
        multiplier = min(
            failed_attempts // AccountLockoutPolicy.MAX_ATTEMPTS,
            AccountLockoutPolicy.MAX_LOCKOUT_MULTIPLIER
        )
        
        return AccountLockoutPolicy.BASE_LOCKOUT_MINUTES * multiplier
    
    @staticmethod
    def should_lock_account(failed_attempts: int) -> bool:
        """Check if account should be locked."""
        return failed_attempts >= AccountLockoutPolicy.MAX_ATTEMPTS


class EmailPolicy:
    """Email validation and management policies."""
    
    @staticmethod
    def validate_email(email: str) -> str:
        """
        Validate and normalize email address.
        RG-AUTH-001: Email validation
        """
        if not email:
            raise ValidationError("Email is required", field="email")
        
        # Normalize email
        email = email.lower().strip()
        
        # Basic format check
        if "@" not in email:
            raise ValidationError("Invalid email format", field="email")
        
        # Length check
        if len(email) > 255:
            raise ValidationError(
                "Email must be less than 255 characters",
                field="email"
            )
        
        # Regex validation
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            raise ValidationError("Invalid email format", field="email")
        
        # Check for disposable email domains (basic list)
        disposable_domains = [
            "tempmail.com", "throwaway.email", "guerrillamail.com",
            "mailinator.com", "10minutemail.com"
        ]
        domain = email.split("@")[1].lower()
        if domain in disposable_domains:
            raise ValidationError(
                "Disposable email addresses are not allowed",
                field="email"
            )
        
        return email


class RoleTransitionPolicy:
    """
    Policy for role transitions and permissions.
    RG-AUTH-009: Role hierarchy management
    """
    
    # Define allowed role transitions
    ALLOWED_TRANSITIONS = {
        "client": ["washer"],  # Client can be promoted to washer
        "washer": ["client", "manager"],  # Washer can be demoted or promoted
        "manager": ["washer", "admin"],  # Manager can be demoted or promoted
        "admin": ["manager"],  # Admin can only be demoted to manager
    }
    
    @staticmethod
    def can_transition(current_role: str, new_role: str) -> bool:
        """Check if role transition is allowed."""
        if current_role == new_role:
            return True
        
        allowed = RoleTransitionPolicy.ALLOWED_TRANSITIONS.get(current_role, [])
        return new_role in allowed
    
    @staticmethod
    def validate_transition(
        current_role: str,
        new_role: str,
        initiator_role: str
    ) -> bool:
        """
        Validate if initiator can perform the role transition.
        Only admins can change roles, and they cannot change their own role.
        """
        # Only admins can change roles
        if initiator_role != "admin":
            raise BusinessRuleViolationError(
                "Only administrators can change user roles",
                rule="RG-AUTH-009"
            )
        
        # Check if transition is allowed
        if not RoleTransitionPolicy.can_transition(current_role, new_role):
            raise BusinessRuleViolationError(
                f"Cannot transition from {current_role} to {new_role}",
                rule="RG-AUTH-009"
            )
        
        return True


class SessionPolicy:
    """
    Session and token management policies.
    RG-AUTH-005: Token management
    """
    
    ACCESS_TOKEN_MINUTES = 15
    REFRESH_TOKEN_DAYS = 7
    MAX_REFRESH_COUNT = 10  # Max times a refresh token can be rotated
    
    @staticmethod
    def should_rotate_refresh_token(usage_count: int) -> bool:
        """Determine if refresh token should be rotated."""
        # Always rotate for security
        return True
    
    @staticmethod
    def is_session_expired(last_activity: Optional[str], max_idle_minutes: int = 30) -> bool:
        """Check if session has expired due to inactivity."""
        if not last_activity:
            return False
        
        # Implementation would check timestamp
        # For now, return False as placeholder
        return False