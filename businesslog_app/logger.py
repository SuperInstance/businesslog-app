"""AppLogger — the main user-facing logger with context support."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Sequence

from .entry import LogEntry, LogLevel
from .filter import LogFilter
from .handler import Handler, ConsoleHandler
from .formatter import ColoredFormatter


class AppLogger:
    """Structured application logger with contexts, tags, and handlers.

    Usage::

        log = AppLogger("myapp")
        log.info("Server started", fields={"port": 8080}, tags=["server"])

        with log.context(request_id="abc123"):
            log.info("Processing request")

        log.warning("Slow query", tags=["database", "performance"])
    """

    def __init__(
        self,
        name: str,
        *,
        handlers: Optional[List[Handler]] = None,
        filters: Optional[List[LogFilter]] = None,
        level: LogLevel = LogLevel.TRACE,
        default_tags: Optional[List[str]] = None,
    ) -> None:
        self.name = name
        self.handlers: List[Handler] = handlers or [
            ConsoleHandler(formatter=ColoredFormatter())
        ]
        self.filters: List[LogFilter] = filters or []
        self.level = level
        self.default_tags: List[str] = list(default_tags or [])
        self._context_stack: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Context management
    # ------------------------------------------------------------------

    @contextmanager
    def context(self, **fields: Any):
        """Push temporary fields onto the context stack."""
        self._context_stack.append(fields)
        try:
            yield self
        finally:
            self._context_stack.pop()

    def _merged_fields(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Merge all context layers plus any per-call fields."""
        merged: Dict[str, Any] = {}
        for layer in self._context_stack:
            merged.update(layer)
        if extra:
            merged.update(extra)
        return merged

    def _merged_tags(self, tags: Optional[List[str]] = None) -> List[str]:
        base = list(self.default_tags)
        if tags:
            base.extend(tags)
        return base

    # ------------------------------------------------------------------
    # Core emit
    # ------------------------------------------------------------------

    def _should_log(self, entry: LogEntry) -> bool:
        if entry.level.value < self.level.value:
            return False
        return all(f.matches(entry) for f in self.filters)

    def _emit(self, entry: LogEntry) -> None:
        if not self._should_log(entry):
            return
        for handler in self.handlers:
            handler.emit(entry)

    # ------------------------------------------------------------------
    # Public convenience methods
    # ------------------------------------------------------------------

    def log(
        self,
        level: LogLevel,
        message: str,
        *,
        fields: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> LogEntry:
        entry = LogEntry.create(
            level=level,
            message=message,
            fields=self._merged_fields(fields),
            tags=self._merged_tags(tags),
            source=self.name,
        )
        self._emit(entry)
        return entry

    def trace(self, message: str, **kwargs: Any) -> LogEntry:
        return self.log(LogLevel.TRACE, message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> LogEntry:
        return self.log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> LogEntry:
        return self.log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> LogEntry:
        return self.log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> LogEntry:
        return self.log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> LogEntry:
        return self.log(LogLevel.CRITICAL, message, **kwargs)

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    def add_handler(self, handler: Handler) -> None:
        self.handlers.append(handler)

    def remove_handler(self, handler: Handler) -> None:
        self.handlers.remove(handler)

    def add_filter(self, f: LogFilter) -> None:
        self.filters.append(f)

    def remove_filter(self, f: LogFilter) -> None:
        self.filters.remove(f)
