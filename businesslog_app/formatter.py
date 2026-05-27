"""Formatter — serialise LogEntry objects to strings."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict

from .entry import LogEntry, LogLevel

# ANSI colour codes
_ANSI = {
    LogLevel.TRACE: "\033[90m",      # grey
    LogLevel.DEBUG: "\033[36m",      # cyan
    LogLevel.INFO: "\033[32m",       # green
    LogLevel.WARNING: "\033[33m",    # yellow
    LogLevel.ERROR: "\033[31m",      # red
    LogLevel.CRITICAL: "\033[1;31m", # bold red
}
_RESET = "\033[0m"


class Formatter(ABC):
    """Base class for log formatters."""

    @abstractmethod
    def format(self, entry: LogEntry) -> str:
        """Convert a LogEntry to a formatted string."""
        ...


class JSONFormatter(Formatter):
    """Format log entries as JSON lines."""

    def __init__(self, indent: int | None = None) -> None:
        self.indent = indent

    def format(self, entry: LogEntry) -> str:
        return json.dumps(entry.to_dict(), indent=self.indent, default=str)


class TextFormatter(Formatter):
    """Human-readable plain-text formatter.

    Output looks like:
        2025-01-15T10:30:00+00:00 [INFO] Something happened  user_id=42  [request]
    """

    def format(self, entry: LogEntry) -> str:
        ts = entry.timestamp.isoformat()
        level = entry.level.name
        parts: list[str] = [f"{ts} [{level}] {entry.message}"]

        if entry.source:
            parts.append(f"src={entry.source}")
        for k, v in entry.fields.items():
            parts.append(f"{k}={v}")
        if entry.tags:
            parts.append("[" + ", ".join(entry.tags) + "]")

        return "  ".join(parts)


class ColoredFormatter(Formatter):
    """Like TextFormatter but with ANSI colours for terminal output."""

    def format(self, entry: LogEntry) -> str:
        ts = entry.timestamp.isoformat()
        level = entry.level.name
        colour = _ANSI.get(entry.level, "")

        parts: list[str] = [f"{ts} [{colour}{level}{_RESET}] {entry.message}"]

        if entry.source:
            parts.append(f"src={entry.source}")
        for k, v in entry.fields.items():
            parts.append(f"{k}={v}")
        if entry.tags:
            parts.append("[" + ", ".join(entry.tags) + "]")

        return "  ".join(parts)
