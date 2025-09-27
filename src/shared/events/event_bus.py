"""
Event Bus for inter-module communication
"""
from typing import Dict, List, Callable, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class DomainEvent(ABC):
    """Base class for all domain events"""
    
    def __post_init__(self):
        if not hasattr(self, 'event_id') or self.event_id is None:
            self.event_id = str(uuid4())
        if not hasattr(self, 'timestamp') or self.timestamp is None:
            self.timestamp = datetime.utcnow()


class EventBus:
    """Simple in-memory event bus for inter-module communication"""
    
    def __init__(self):
        self._handlers: Dict[type, List[Callable]] = {}
        self._middlewares: List[Callable] = []
    
    def subscribe(self, event_type: type, handler: Callable):
        """Subscribe to an event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(f"Subscribed {handler.__name__} to {event_type.__name__}")
    
    def add_middleware(self, middleware: Callable):
        """Add middleware to process all events"""
        self._middlewares.append(middleware)
    
    async def publish(self, event: DomainEvent):
        """Publish an event to all subscribers"""
        event_type = type(event)
        
        # Process middlewares first
        for middleware in self._middlewares:
            try:
                if asyncio.iscoroutinefunction(middleware):
                    await middleware(event)
                else:
                    middleware(event)
            except Exception as e:
                logger.error(f"Event middleware error: {e}")
        
        # Process event handlers
        if event_type in self._handlers:
            tasks = []
            for handler in self._handlers[event_type]:
                tasks.append(self._safe_handler_call(handler, event))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _safe_handler_call(self, handler: Callable, event: DomainEvent):
        """Safely call event handler with error handling"""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            logger.error(f"Event handler {handler.__name__} failed: {e}")


# Global event bus instance
_event_bus: EventBus = None


def get_event_bus() -> EventBus:
    """Get global event bus instance"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus