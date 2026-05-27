"""Handlers — destinations that receive formatted log entries."""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, List, Optional, TextIO

from .entry import LogEntry
from .formatter import Formatter, TextFormatter


class Handler(ABC):
    """Base class for all log handlers."""

    def __init__(self, formatter: Optional[Formatter] = None) -> None:
        self.formatter = formatter or TextFormatter()

    @abstractmethod
    def emit(self, entry: LogEntry) -> None:
        """Process a single log entry."""
        ...

    def format(self, entry: LogEntry) -> str:
        """Format an entry using this handler's formatter."""
        return self.formatter.format(entry)


class ConsoleHandler(Handler):
    """Write log entries to a stream (default: stderr)."""

    def __init__(
        self,
        formatter: Optional[Formatter] = None,
        stream: Optional[TextIO] = None,
    ) -> None:
        super().__init__(formatter)
        self.stream = stream or sys.stderr

    def emit(self, entry: LogEntry) -> None:
        line = self.format(entry)
        self.stream.write(line + "\n")
        self.stream.flush()


class FileHandler(Handler):
    """Append log entries to a file."""

    def __init__(
        self,
        path: str | Path,
        formatter: Optional[Formatter] = None,
        encoding: str = "utf-8",
    ) -> None:
        super().__init__(formatter)
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._encoding = encoding

    def emit(self, entry: LogEntry) -> None:
        line = self.format(entry)
        with self.path.open("a", encoding=self._encoding) as fh:
            fh.write(line + "\n")


class MemoryHandler(Handler):
    """Buffer log entries in memory for later inspection."""

    def __init__(self, formatter: Optional[Formatter] = None, maxsize: int = 10_000) -> None:
        super().__init__(formatter)
        self.maxsize = maxsize
        self.entries: List[LogEntry] = []

    def emit(self, entry: LogEntry) -> None:
        self.entries.append(entry)
        if len(self.entries) > self.maxsize:
            self.entries = self.entries[-self.maxsize:]

    def clear(self) -> None:
        """Remove all buffered entries."""
        self.entries.clear()

    def get_entries(self) -> List[LogEntry]:
        """Return a snapshot of buffered entries."""
        return list(self.entries)


class CallbackHandler(Handler):
    """Forward log entries to an arbitrary callback."""

    def __init__(
        self,
        callback: Callable[[LogEntry], None],
        formatter: Optional[Formatter] = None,
    ) -> None:
        super().__init__(formatter)
        self.callback = callback

    def emit(self, entry: LogEntry) -> None:
        self.callback(entry)
