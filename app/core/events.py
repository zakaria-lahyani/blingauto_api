"""
In-memory Event Bus for Domain Events
Provides pub/sub pattern for decoupled event handling
"""

from typing import Dict, List, Callable, Any
from collections import defaultdict
import asyncio
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """
    Simple in-memory event bus for domain events.

    Supports:
    - Event publishing (fire and forget)
    - Event subscription (multiple handlers per event)
    - Async event handlers
    """

    def __init__(self):
        """Initialize event bus with empty subscribers."""
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: Callable) -> None:
        """
        Subscribe a handler to an event.

        Args:
            event_name: Name of the event to listen for
            handler: Async callable to handle the event
        """
        if handler not in self._subscribers[event_name]:
            self._subscribers[event_name].append(handler)
            logger.info(f"Subscribed handler {handler.__name__} to event {event_name}")

    def unsubscribe(self, event_name: str, handler: Callable) -> None:
        """
        Unsubscribe a handler from an event.

        Args:
            event_name: Name of the event
            handler: Handler to remove
        """
        if handler in self._subscribers[event_name]:
            self._subscribers[event_name].remove(handler)
            logger.info(f"Unsubscribed handler {handler.__name__} from event {event_name}")

    async def publish(self, event_name: str, event_data: Dict[str, Any]) -> bool:
        """
        Publish an event to all subscribers.

        Args:
            event_name: Name of the event
            event_data: Event payload

        Returns:
            True if event was published (doesn't guarantee all handlers succeeded)
        """
        handlers = self._subscribers.get(event_name, [])

        if not handlers:
            logger.debug(f"No subscribers for event {event_name}")
            return True

        logger.info(f"Publishing event {event_name} to {len(handlers)} handlers")

        # Execute all handlers concurrently (fire and forget)
        tasks = []
        for handler in handlers:
            try:
                task = asyncio.create_task(self._execute_handler(handler, event_name, event_data))
                tasks.append(task)
            except Exception as e:
                logger.error(f"Failed to create task for handler {handler.__name__}: {str(e)}")

        # Wait for all handlers to complete (with timeout)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        return True

    async def _execute_handler(
        self,
        handler: Callable,
        event_name: str,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Execute a single event handler with error handling.

        Args:
            handler: Event handler function
            event_name: Name of the event
            event_data: Event payload
        """
        try:
            # Call handler (supports both sync and async)
            if asyncio.iscoroutinefunction(handler):
                await handler(event_data)
            else:
                handler(event_data)

            logger.debug(f"Handler {handler.__name__} completed for event {event_name}")

        except Exception as e:
            # Log error but don't propagate - event handlers should not break the flow
            logger.error(
                f"Error in event handler {handler.__name__} for event {event_name}: {str(e)}",
                exc_info=True
            )

    def clear_all_subscribers(self) -> None:
        """Clear all event subscribers (useful for testing)."""
        self._subscribers.clear()
        logger.info("Cleared all event subscribers")

    def get_subscriber_count(self, event_name: str) -> int:
        """Get number of subscribers for an event."""
        return len(self._subscribers.get(event_name, []))


# Global event bus instance
event_bus = EventBus()


# Example usage and event handler decorators
def on_event(event_name: str):
    """
    Decorator to register a function as an event handler.

    Usage:
        @on_event("booking.created")
        async def handle_booking_created(event_data):
            # Handle the event
            pass
    """
    def decorator(func: Callable):
        event_bus.subscribe(event_name, func)
        return func
    return decorator
