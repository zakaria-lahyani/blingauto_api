"""
Système d'événements simplifié
"""
import asyncio
import logging
from typing import Any, Dict, List, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

EventHandler = Callable[[Dict[str, Any]], Awaitable[None]]


@dataclass
class Event:
    """Événement simple"""
    name: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str = "unknown"


class SimpleEventBus:
    """Bus d'événements simple en mémoire"""
    
    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._middleware: List[EventHandler] = []
    
    def subscribe(self, event_name: str, handler: EventHandler):
        """S'abonne à un événement"""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
        logger.debug(f"Handler subscribed to event: {event_name}")
    
    def unsubscribe(self, event_name: str, handler: EventHandler):
        """Se désabonne d'un événement"""
        if event_name in self._handlers:
            try:
                self._handlers[event_name].remove(handler)
                logger.debug(f"Handler unsubscribed from event: {event_name}")
            except ValueError:
                pass
    
    def add_middleware(self, middleware: EventHandler):
        """Ajoute un middleware (appelé pour tous les événements)"""
        self._middleware.append(middleware)
    
    async def publish(self, event_name: str, data: Dict[str, Any], source: str = "unknown"):
        """Publie un événement"""
        event = Event(
            name=event_name,
            data=data,
            timestamp=datetime.utcnow(),
            source=source
        )
        
        # Appel des middlewares
        for middleware in self._middleware:
            try:
                await middleware(event.__dict__)
            except Exception as e:
                logger.error(f"Middleware error for event {event_name}: {e}")
        
        # Appel des handlers spécifiques
        handlers = self._handlers.get(event_name, [])
        if handlers:
            tasks = []
            for handler in handlers:
                try:
                    task = asyncio.create_task(handler(event.__dict__))
                    tasks.append(task)
                except Exception as e:
                    logger.error(f"Handler error for event {event_name}: {e}")
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.debug(f"Event published: {event_name} with {len(handlers)} handlers")
    
    def list_events(self) -> List[str]:
        """Liste tous les événements avec des handlers"""
        return list(self._handlers.keys())
    
    def get_handler_count(self, event_name: str) -> int:
        """Nombre de handlers pour un événement"""
        return len(self._handlers.get(event_name, []))


# Instance globale
_event_bus: SimpleEventBus = SimpleEventBus()


def get_event_bus() -> SimpleEventBus:
    """Récupère le bus d'événements global"""
    return _event_bus


async def publish_event(event_name: str, data: Dict[str, Any], source: str = "unknown"):
    """Raccourci pour publier un événement"""
    await _event_bus.publish(event_name, data, source)


def subscribe_to_event(event_name: str):
    """Décorateur pour s'abonner à un événement"""
    def decorator(func: EventHandler):
        _event_bus.subscribe(event_name, func)
        return func
    return decorator


# Middleware de logging par défaut
async def logging_middleware(event_data: Dict[str, Any]):
    """Middleware qui log tous les événements"""
    logger.info(f"Event: {event_data['name']} from {event_data['source']}")


# Ajouter le middleware de logging
_event_bus.add_middleware(logging_middleware)