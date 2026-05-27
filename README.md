# BusinessLog App

Structured application-level logging for Python — zero external dependencies.

## Features

- **Structured log entries** with levels, fields, tags, and source tracking
- **Flexible handlers** — console, file, in-memory buffer, or custom callback
- **Composable filters** — by level, tags, field values, or arbitrary predicates
- **Multiple formatters** — JSON, plain text, or colored terminal output
- **Context support** — push/pop contextual fields that merge into every log entry
- **Fully typed** — dataclasses + type hints, no external deps beyond pytest

## Quick Start

```python
from businesslog_app import AppLogger, LogLevel

log = AppLogger("myapp")

log.info("Server started", fields={"port": 8080}, tags=["server"])

with log.context(request_id="abc123"):
    log.info("Processing request")
    log.warning("Slow query", fields={"duration_ms": 1200}, tags=["database"])

log.error("Connection lost", fields={"host": "db.internal"}, tags=["database", "critical"])
```

## Architecture

```
businesslog_app/
├── __init__.py      # Public API re-exports
├── entry.py         # LogEntry + LogLevel
├── logger.py        # AppLogger with context support
├── handler.py       # Console, File, Memory, Callback handlers
├── filter.py        # Level, Tag, Field, Predicate, Composite filters
└── formatter.py     # JSON, Text, Colored formatters
```

## Handlers

| Handler | Description |
|---|---|
| `ConsoleHandler` | Write to stderr (or any stream) |
| `FileHandler` | Append to a file, auto-creates parent dirs |
| `MemoryHandler` | Buffer in memory with optional max size |
| `CallbackHandler` | Forward to any `Callable[[LogEntry], None]` |

## Filters

| Filter | Description |
|---|---|
| `LevelFilter` | Minimum log level |
| `TagFilter` | Match by tags (any/all/none modes) |
| `FieldFilter` | Match required field values or existence |
| `PredicateFilter` | Custom function |
| `CompositeFilter` | Combine filters with AND/OR logic |

## Running Tests

```bash
python -m pytest tests/ -q
```

## License

MIT
