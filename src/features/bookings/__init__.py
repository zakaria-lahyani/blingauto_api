"""
Bookings Feature - Auto-discoverable booking management system
"""

from fastapi import APIRouter
from .config import BookingsConfig


def get_router() -> APIRouter:
    """Récupère le router de la feature bookings"""
    from .presentation.api.router import router
    return router


def get_config():
    """Récupère la configuration de la feature bookings"""
    return BookingsConfig()


async def initialize():
    """Initialise la feature bookings"""
    pass


async def shutdown():
    """Nettoie la feature bookings"""
    pass


__all__ = [
    'get_router',
    'get_config',
    'initialize',
    'shutdown'
]