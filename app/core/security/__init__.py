from .password import password_hasher
from .jwt import jwt_handler, JWTHandler

# Create convenience functions
encode = JWTHandler.create_token
decode = JWTHandler.decode_token
from .rbac import Role, Permission, RBACService, rbac_service, require_permissions

__all__ = [
    "password_hasher",
    "jwt_handler", 
    "JWTHandler",
    "encode",
    "decode",
    "Role",
    "Permission",
    "RBACService",
    "rbac_service",
    "require_permissions",
]