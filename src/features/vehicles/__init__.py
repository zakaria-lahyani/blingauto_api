"""
Vehicles Feature - Auto-discoverable vehicle management system
"""

from fastapi import APIRouter
from .config import VehicleConfig


def get_router() -> APIRouter:
    """Récupère le router de la feature vehicles"""
    from .presentation.api.router import router
    return router


def get_config():
    """Récupère la configuration de la feature vehicles"""
    return VehicleConfig()


async def initialize():
    """Initialise la feature vehicles"""
    pass


async def shutdown():
    """Nettoie la feature vehicles"""
    pass


__all__ = [
    'get_router',
    'get_config', 
    'initialize',
    'shutdown'
]