"""
Event system for inter-module communication
"""

from src.shared.events.event_bus import EventBus, DomainEvent, get_event_bus

__all__ = ['EventBus', 'DomainEvent', 'get_event_bus']