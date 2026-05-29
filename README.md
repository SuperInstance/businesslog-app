# businesslog-app

**Structured application-level logging for Python** — zero external dependencies. Console, file, memory, and custom handlers with composable filters.

## What This Gives You

- **Structured entries** — levels, fields, tags, source tracking, and trace context
- **Flexible handlers** — console, file, in-memory buffer, custom callback
- **Composable filters** — by level, tags, field values, or arbitrary predicates
- **Multiple formatters** — JSON, plain text, or colored terminal output
- **Context support** — push/pop contextual fields that merge into every entry

## Installation

```bash
pip install businesslog-app
```

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

## Handlers

| Handler | Description |
|---------|-------------|
| `ConsoleHandler` | Write to stderr (or any stream) |
| `FileHandler` | Append to a file, auto-creates parent dirs |
| `MemoryHandler` | Buffer in memory with optional max size |
| `CallbackHandler` | Forward to any `Callable[[LogEntry], None]` |

## Filters

Chain filters with `&` (and) / `|` (or): `LevelFilter(LogLevel.ERROR) & TagFilter("database")`

## Testing

```bash
pip install -e .
pytest
```

## License

MIT
