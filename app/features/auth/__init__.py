"""
Auth Feature Module

Implements authentication and authorization using hexagonal architecture.
Follows business rules defined in REGLES_DE_GESTION.md.

Architecture:
- domain/: Pure business logic with no framework dependencies
- ports/: Interfaces/contracts for external dependencies  
- use_cases/: Application layer orchestrating domain logic
- adapters/: Infrastructure implementations of ports
- api/: HTTP/REST interface layer
"""

from .api import auth_router, CurrentUser, AdminUser, StaffUser
from .domain import User, UserRole, UserStatus

__all__ = [
    "auth_router",
    "CurrentUser", 
    "AdminUser",
    "StaffUser",
    "User",
    "UserRole", 
    "UserStatus",
]