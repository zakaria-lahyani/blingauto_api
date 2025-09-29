"""
Scheduling Feature - Auto-discoverable scheduling management system
"""

from fastapi import APIRouter
from .config import SchedulingConfig


def get_router() -> APIRouter:
    """Récupère le router de la feature scheduling"""
    from .presentation.api.router import router
    return router


def get_config():
    """Récupère la configuration de la feature scheduling"""
    return SchedulingConfig()


async def initialize():
    """Initialise la feature scheduling"""
    pass


async def shutdown():
    """Nettoie la feature scheduling"""
    pass


__all__ = [
    'get_router',
    'get_config',
    'initialize',
    'shutdown'
]