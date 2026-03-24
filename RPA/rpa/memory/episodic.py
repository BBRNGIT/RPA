"""
Episodic Memory for the RPA system.

Episodic Memory stores events, learning sessions, and experiences.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class EventType(Enum):
    """Types of events in episodic memory."""
    PATTERN_LEARNED = "pattern_learned"
    PATTERN_VALIDATED = "pattern_validated"
    PATTERN_CONSOLIDATED = "pattern_consolidated"
    PATTERN_REJECTED = "pattern_rejected"
    GAP_DETECTED = "gap_detected"
    INQUIRY_CREATED = "inquiry_created"
    INQUIRY_ANSWERED = "inquiry_answered"
    CORRECTION_APPLIED = "correction_applied"
    ASSESSMENT_COMPLETED = "assessment_completed"
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    ERROR_OCCURRED = "error_occurred"
    CODE_EXECUTED = "code_executed"


@dataclass
class Event:
    """Represents an event in episodic memory."""
    event_id: str
    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None
    pattern_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "pattern_id": self.pattern_id,
            "data": self.data,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Deserialize from dictionary."""
        return cls(
            event_id=data["event_id"],
            event_type=EventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            session_id=data.get("session_id"),
            pattern_id=data.get("pattern_id"),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
        )


class EpisodicMemory:
    """
    Episodic Memory for event logging.
    
    Stores events related to learning sessions, pattern operations,
    and system experiences. Provides querying and replay capabilities.
    """
    
    def __init__(self, max_events: int = 10000):
        """
        Initialize Episodic Memory.
        
        Args:
            max_events: Maximum number of events to store
        """
        self.max_events = max_events
        self._events: List[Event] = []
        self._event_index: Dict[str, Event] = {}
        self._session_index: Dict[str, List[str]] = {}
        self._pattern_index: Dict[str, List[str]] = {}
    
    def log_event(
        self,
        event_type: EventType,
        session_id: Optional[str] = None,
        pattern_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Event:
        """
        Log an event.
        
        Args:
            event_type: Type of event
            session_id: Optional session ID
            pattern_id: Optional pattern ID
            data: Event-specific data
            metadata: Additional metadata
            
        Returns:
            The created event
        """
        event = Event(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            event_type=event_type,
            session_id=session_id,
            pattern_id=pattern_id,
            data=data or {},
            metadata=metadata or {},
        )
        
        self._events.append(event)
        self._event_index[event.event_id] = event
        
        # Update indices
        if session_id:
            if session_id not in self._session_index:
                self._session_index[session_id] = []
            self._session_index[session_id].append(event.event_id)
        
        if pattern_id:
            if pattern_id not in self._pattern_index:
                self._pattern_index[pattern_id] = []
            self._pattern_index[pattern_id].append(event.event_id)
        
        # Enforce max events
        self._enforce_max_events()
        
        return event
    
    def get_event(self, event_id: str) -> Optional[Event]:
        """Get an event by ID."""
        return self._event_index.get(event_id)
    
    def get_events_by_type(self, event_type: EventType) -> List[Event]:
        """Get all events of a specific type."""
        return [e for e in self._events if e.event_type == event_type]
    
    def get_events_by_session(self, session_id: str) -> List[Event]:
        """Get all events for a session."""
        event_ids = self._session_index.get(session_id, [])
        return [
            self._event_index[eid] 
            for eid in event_ids 
            if eid in self._event_index
        ]
    
    def get_events_by_pattern(self, pattern_id: str) -> List[Event]:
        """Get all events for a pattern."""
        event_ids = self._pattern_index.get(pattern_id, [])
        return [
            self._event_index[eid] 
            for eid in event_ids 
            if eid in self._event_index
        ]
    
    def get_events_in_range(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> List[Event]:
        """Get events within a time range."""
        return [
            e for e in self._events
            if start_time <= e.timestamp <= end_time
        ]
    
    def get_recent_events(self, count: int = 10) -> List[Event]:
        """Get the most recent events."""
        return self._events[-count:]
    
    def replay_session(self, session_id: str) -> List[Event]:
        """
        Replay all events from a session.
        
        Returns events in chronological order.
        """
        events = self.get_events_by_session(session_id)
        return sorted(events, key=lambda e: e.timestamp)
    
    def get_event_count(self) -> int:
        """Get total event count."""
        return len(self._events)
    
    def get_event_count_by_type(self) -> Dict[str, int]:
        """Get event counts by type."""
        counts: Dict[str, int] = {}
        for event in self._events:
            type_name = event.event_type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts
    
    def _enforce_max_events(self) -> None:
        """Enforce maximum event count by removing oldest events."""
        while len(self._events) > self.max_events:
            removed = self._events.pop(0)
            del self._event_index[removed.event_id]
            
            # Clean up indices
            if removed.session_id:
                self._session_index[removed.session_id] = [
                    eid for eid in self._session_index.get(removed.session_id, [])
                    if eid != removed.event_id
                ]
            
            if removed.pattern_id:
                self._pattern_index[removed.pattern_id] = [
                    eid for eid in self._pattern_index.get(removed.pattern_id, [])
                    if eid != removed.event_id
                ]
    
    def clear(self) -> None:
        """Clear all events."""
        self._events.clear()
        self._event_index.clear()
        self._session_index.clear()
        self._pattern_index.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "max_events": self.max_events,
            "events": [e.to_dict() for e in self._events],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EpisodicMemory":
        """Deserialize from dictionary."""
        memory = cls(max_events=data.get("max_events", 10000))
        
        for event_data in data.get("events", []):
            event = Event.from_dict(event_data)
            memory._events.append(event)
            memory._event_index[event.event_id] = event
            
            if event.session_id:
                if event.session_id not in memory._session_index:
                    memory._session_index[event.session_id] = []
                memory._session_index[event.session_id].append(event.event_id)
            
            if event.pattern_id:
                if event.pattern_id not in memory._pattern_index:
                    memory._pattern_index[event.pattern_id] = []
                memory._pattern_index[event.pattern_id].append(event.event_id)
        
        return memory
    
    def __len__(self) -> int:
        """Return number of events."""
        return len(self._events)
    
    def __repr__(self) -> str:
        return f"EpisodicMemory(events={len(self._events)})"
