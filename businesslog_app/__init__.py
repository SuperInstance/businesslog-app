"""businesslog-app — structured application-level logging for Python."""

from .entry import LogEntry
from .logger import AppLogger
from .handler import ConsoleHandler, FileHandler, MemoryHandler, CallbackHandler
from .filter import LogFilter, LevelFilter, TagFilter, FieldFilter
from .formatter import JSONFormatter, TextFormatter, ColoredFormatter

__version__ = "1.0.0"
__all__ = [
    "LogEntry",
    "AppLogger",
    "ConsoleHandler",
    "FileHandler",
    "MemoryHandler",
    "CallbackHandler",
    "LogFilter",
    "LevelFilter",
    "TagFilter",
    "FieldFilter",
    "JSONFormatter",
    "TextFormatter",
    "ColoredFormatter",
]
