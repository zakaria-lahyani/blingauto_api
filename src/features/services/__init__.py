"""
Services Feature - Auto-discoverable service management system  
"""

from fastapi import APIRouter
from .config import ServicesConfig


def get_router() -> APIRouter:
    """Récupère le router de la feature services"""
    from .presentation.api.router import router
    return router


def get_config():
    """Récupère la configuration de la feature services"""
    return ServicesConfig()


async def initialize():
    """Initialise la feature services"""
    pass


async def shutdown():
    """Nettoie la feature services"""
    pass


__all__ = [
    'get_router',
    'get_config',
    'initialize', 
    'shutdown'
]