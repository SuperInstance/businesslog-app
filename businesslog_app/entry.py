"""LogEntry — the core data structure for a single log record."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class LogLevel(Enum):
    """Standard log levels ordered by severity."""

    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    def __lt__(self, other: object) -> bool:
        if isinstance(other, LogLevel):
            return self.value < other.value
        return NotImplemented

    def __le__(self, other: object) -> bool:
        if isinstance(other, LogLevel):
            return self.value <= other.value
        return NotImplemented

    def __gt__(self, other: object) -> bool:
        if isinstance(other, LogLevel):
            return self.value > other.value
        return NotImplemented

    def __ge__(self, other: object) -> bool:
        if isinstance(other, LogLevel):
            return self.value >= other.value
        return NotImplemented


@dataclass(frozen=True)
class LogEntry:
    """An immutable, structured log record.

    Attributes:
        level: Severity level.
        message: Human-readable log message.
        timestamp: UTC datetime when the entry was created.
        fields: Arbitrary structured key-value data.
        tags: Short labels for categorisation and filtering.
        source: Identifier for the origin (module, class, etc.).
        entry_id: Unique identifier for this entry.
    """

    level: LogLevel
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    fields: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    source: Optional[str] = None
    entry_id: str = field(default_factory=lambda: uuid.uuid4().hex)

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        level: LogLevel,
        message: str,
        *,
        fields: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> "LogEntry":
        """Build a LogEntry with keyword-only optional params."""
        return cls(
            level=level,
            message=message,
            timestamp=timestamp or datetime.now(timezone.utc),
            fields=fields or {},
            tags=tags or [],
            source=source,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def with_fields(self, **extra: Any) -> "LogEntry":
        """Return a new entry with additional fields merged in."""
        merged = {**self.fields, **extra}
        return LogEntry(
            level=self.level,
            message=self.message,
            timestamp=self.timestamp,
            fields=merged,
            tags=list(self.tags),
            source=self.source,
            entry_id=self.entry_id,
        )

    def with_tags(self, *extra: str) -> "LogEntry":
        """Return a new entry with additional tags."""
        merged = list(set(self.tags) | set(extra))
        return LogEntry(
            level=self.level,
            message=self.message,
            timestamp=self.timestamp,
            fields=dict(self.fields),
            tags=merged,
            source=self.source,
            entry_id=self.entry_id,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dict."""
        return {
            "entry_id": self.entry_id,
            "level": self.level.name,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "fields": dict(self.fields),
            "tags": list(self.tags),
            "source": self.source,
        }
