"""
Auth Feature - Auto-discoverable authentication system
"""

from fastapi import APIRouter
from .config import AuthConfig
from .auth_module import AuthModule
from .domain.entities import AuthUser
from .domain.enums import AuthRole

# Instance globale du module auth
_auth_module = None


def get_router() -> APIRouter:
    """Récupère le router de la feature auth"""
    from .presentation.api.router import create_auth_router
    
    global _auth_module
    if _auth_module is None:
        config = AuthConfig()
        _auth_module = AuthModule(config)
    
    return create_auth_router(_auth_module)


def get_config() -> AuthConfig:
    """Récupère la configuration de la feature auth"""
    return AuthConfig()


async def initialize():
    """Initialise la feature auth"""
    global _auth_module
    if _auth_module is None:
        config = AuthConfig()
        _auth_module = AuthModule(config)
    
    await _auth_module.initialize()


async def shutdown():
    """Nettoie la feature auth"""
    global _auth_module
    if _auth_module is not None:
        await _auth_module.shutdown()


def get_auth_module() -> AuthModule:
    """Récupère l'instance du module auth"""
    global _auth_module
    if _auth_module is None:
        config = AuthConfig()
        _auth_module = AuthModule(config)
    return _auth_module


__all__ = [
    'AuthModule', 
    'AuthConfig', 
    'AuthUser', 
    'AuthRole',
    'get_router',
    'get_config',
    'initialize',
    'shutdown',
    'get_auth_module'
]