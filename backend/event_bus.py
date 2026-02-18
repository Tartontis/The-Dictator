import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

class EventBus:
    _instance = None
    _subscribers: dict[str, list[Callable]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._subscribers = {}
        return cls._instance

    @classmethod
    def subscribe(cls, event_type: str, callback: Callable[[Any], None]):
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []
        cls._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type}")

    @classmethod
    def publish(cls, event_type: str, data: Any = None):
        if event_type in cls._subscribers:
            for callback in cls._subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in subscriber for {event_type}: {e}")
        logger.debug(f"Published {event_type}: {data}")

    @classmethod
    def clear(cls):
        """Clear all subscribers (mostly for testing)."""
        cls._subscribers = {}
