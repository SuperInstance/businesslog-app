"""Filters — decide which log entries should pass through."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional, Set

from .entry import LogEntry, LogLevel


class LogFilter(ABC):
    """Base class for log filters."""

    @abstractmethod
    def matches(self, entry: LogEntry) -> bool:
        """Return True if the entry should be kept."""
        ...


class LevelFilter(LogFilter):
    """Pass entries at or above a minimum level."""

    def __init__(self, min_level: LogLevel) -> None:
        self.min_level = min_level

    def matches(self, entry: LogEntry) -> bool:
        return entry.level.value >= self.min_level.value


class TagFilter(LogFilter):
    """Pass entries that have any of the required tags."""

    def __init__(self, tags: List[str], *, mode: str = "any") -> None:
        """
        Args:
            tags: Tags to match against.
            mode: 'any' — entry must have at least one listed tag.
                  'all' — entry must have every listed tag.
                  'none' — entry must not have any listed tag.
        """
        if mode not in ("any", "all", "none"):
            raise ValueError(f"mode must be 'any', 'all', or 'none', got {mode!r}")
        self.tags: Set[str] = set(tags)
        self.mode = mode

    def matches(self, entry: LogEntry) -> bool:
        entry_tags = set(entry.tags)
        if self.mode == "any":
            return bool(entry_tags & self.tags)
        if self.mode == "all":
            return self.tags.issubset(entry_tags)
        # mode == "none"
        return not (entry_tags & self.tags)


class FieldFilter(LogFilter):
    """Pass entries whose fields match all specified criteria."""

    def __init__(
        self,
        required_fields: Optional[dict[str, Any]] = None,
        *,
        field_exists: Optional[List[str]] = None,
    ) -> None:
        """
        Args:
            required_fields: key-value pairs that must all be present and equal.
            field_exists: keys that must simply exist (value ignored).
        """
        self.required_fields = required_fields or {}
        self.field_exists = field_exists or []

    def matches(self, entry: LogEntry) -> bool:
        for key, value in self.required_fields.items():
            if key not in entry.fields or entry.fields[key] != value:
                return False
        for key in self.field_exists:
            if key not in entry.fields:
                return False
        return True


class PredicateFilter(LogFilter):
    """Pass entries that satisfy an arbitrary predicate function."""

    def __init__(self, predicate: Callable[[LogEntry], bool]) -> None:
        self.predicate = predicate

    def matches(self, entry: LogEntry) -> bool:
        return self.predicate(entry)


class CompositeFilter(LogFilter):
    """Combine multiple filters with AND / OR logic."""

    def __init__(self, *filters: LogFilter, mode: str = "and") -> None:
        if mode not in ("and", "or"):
            raise ValueError(f"mode must be 'and' or 'or', got {mode!r}")
        self.filters = list(filters)
        self.mode = mode

    def matches(self, entry: LogEntry) -> bool:
        if self.mode == "and":
            return all(f.matches(entry) for f in self.filters)
        return any(f.matches(entry) for f in self.filters)
