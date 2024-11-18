# chui/events/base.py

from typing import Callable, Dict, List, Any, TypeVar, Generic, Optional
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from chui.core.errors import EventError

T = TypeVar('T')

@dataclass
class Event(Generic[T]):
    """Base event class for all system events"""
    name: str
    data: T
    timestamp: datetime
    operation_id: Optional[UUID] = None
    source: Optional[str] = None


@dataclass
class OperationContext:
    """Tracks context of an operation across multiple events"""
    operation_id: UUID
    operation_type: str
    start_time: datetime
    status: str = "in_progress"
    metadata: Dict = field(default_factory=dict)
    events: List[Dict] = field(default_factory=list)
    end_time: Optional[datetime] = None
    error: Optional[str] = None

    def add_event(self, event: Event) -> None:
        """Add an event to the operation timeline"""
        self.events.append({
            "timestamp": event.timestamp,
            "name": event.name,
            "data": event.data
        })

    def complete(self, status: str = "completed", error: Optional[str] = None) -> None:
        """Mark operation as complete"""
        self.status = status
        self.end_time = datetime.now()
        self.error = error


class EventManager:
    """Central event management system"""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._wildcard_handlers: List[Callable] = []
        self._active_operations: Dict[UUID, OperationContext] = {}
        self._completed_operations: Dict[UUID, OperationContext] = {}

    def subscribe(self, event_name: str, handler: Callable) -> None:
        """Subscribe to an event"""
        if event_name == "*":
            self._wildcard_handlers.append(handler)
        else:
            if event_name not in self._handlers:
                self._handlers[event_name] = []
            self._handlers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: Callable) -> None:
        """Unsubscribe from an event"""
        if event_name == "*":
            self._wildcard_handlers.remove(handler)
        else:
            self._handlers[event_name].remove(handler)

    def emit(self, event: Event) -> None:
        """Emit an event"""
        # Add event to operation context if it exists
        if event.operation_id and event.operation_id in self._active_operations:
            self._active_operations[event.operation_id].add_event(event)

        # Call specific handlers
        for handler in self._handlers.get(event.name, []):
            try:
                handler(event)
            except Exception as e:
                raise EventError(f"Error in event handler: {str(e)}", e)

        # Call wildcard handlers
        for handler in self._wildcard_handlers:
            try:
                handler(event)
            except Exception as e:
                raise EventError(f"Error in wildcard handler: {str(e)}", e)

    def start_operation(self, operation_type: str, metadata: Dict = None) -> UUID:
        """Start a new operation and get its correlation ID"""
        operation_id = uuid4()
        context = OperationContext(
            operation_id=operation_id,
            operation_type=operation_type,
            start_time=datetime.now(),
            metadata=metadata or {}
        )
        self._active_operations[operation_id] = context
        return operation_id

    def complete_operation(self, operation_id: UUID, status: str = "completed", error: str = None) -> None:
        """Mark an operation as complete"""
        if operation_id not in self._active_operations:
            raise ValueError(f"No active operation found for ID: {operation_id}")

        context = self._active_operations.pop(operation_id)
        context.complete(status, error)
        self._completed_operations[operation_id] = context

    def get_operation_status(self, operation_id: UUID) -> Optional[OperationContext]:
        """Get the current status of an operation"""
        return (
            self._active_operations.get(operation_id) or
            self._completed_operations.get(operation_id)
        )

    def get_operation_timeline(self, operation_id: UUID) -> List[Dict]:
        """Get chronological timeline of operation events"""
        context = self.get_operation_status(operation_id)
        if not context:
            return []
        return sorted(context.events, key=lambda e: e["timestamp"])

    def get_active_operations(self) -> Dict[UUID, OperationContext]:
        """Get all currently active operations"""
        return self._active_operations.copy()

    def cleanup_completed(self, before: datetime = None) -> None:
        """Clean up completed operations before specified time"""
        if not before:
            return

        to_remove = [
            op_id for op_id, context in self._completed_operations.items()
            if context.end_time and context.end_time < before
        ]

        for op_id in to_remove:
            del self._completed_operations[op_id]