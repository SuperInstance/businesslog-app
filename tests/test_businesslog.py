"""Tests for businesslog_app."""

import json
import io
import tempfile
from pathlib import Path

import pytest

from businesslog_app.entry import LogEntry, LogLevel
from businesslog_app.logger import AppLogger
from businesslog_app.handler import (
    ConsoleHandler,
    FileHandler,
    MemoryHandler,
    CallbackHandler,
)
from businesslog_app.filter import (
    LevelFilter,
    TagFilter,
    FieldFilter,
    PredicateFilter,
    CompositeFilter,
)
from businesslog_app.formatter import JSONFormatter, TextFormatter, ColoredFormatter


# ── LogEntry ──────────────────────────────────────────────────────────

class TestLogLevel:
    def test_ordering(self):
        assert LogLevel.DEBUG < LogLevel.INFO
        assert LogLevel.CRITICAL > LogLevel.ERROR
        assert LogLevel.WARNING <= LogLevel.WARNING
        assert LogLevel.INFO >= LogLevel.INFO

    def test_values(self):
        assert LogLevel.TRACE.value == 5
        assert LogLevel.CRITICAL.value == 50


class TestLogEntry:
    def test_create_basic(self):
        e = LogEntry.create(LogLevel.INFO, "hello")
        assert e.level == LogLevel.INFO
        assert e.message == "hello"
        assert e.fields == {}
        assert e.tags == []
        assert e.source is None
        assert e.entry_id  # non-empty

    def test_create_full(self):
        e = LogEntry.create(
            LogLevel.ERROR,
            "boom",
            fields={"code": 500},
            tags=["api", "fatal"],
            source="web",
        )
        assert e.fields["code"] == 500
        assert "api" in e.tags
        assert e.source == "web"

    def test_immutable(self):
        e = LogEntry.create(LogLevel.INFO, "x")
        with pytest.raises(AttributeError):
            e.message = "y"  # type: ignore[misc]

    def test_with_fields(self):
        e = LogEntry.create(LogLevel.INFO, "test", fields={"a": 1})
        e2 = e.with_fields(b=2)
        assert e2.fields == {"a": 1, "b": 2}
        assert e.fields == {"a": 1}  # original unchanged

    def test_with_tags(self):
        e = LogEntry.create(LogLevel.INFO, "test", tags=["a"])
        e2 = e.with_tags("b", "c")
        assert set(e2.tags) == {"a", "b", "c"}

    def test_to_dict(self):
        e = LogEntry.create(LogLevel.INFO, "hello", fields={"k": "v"})
        d = e.to_dict()
        assert d["level"] == "INFO"
        assert d["message"] == "hello"
        assert d["fields"]["k"] == "v"
        assert "timestamp" in d


# ── Formatters ────────────────────────────────────────────────────────

class TestJSONFormatter:
    def test_format(self):
        e = LogEntry.create(LogLevel.INFO, "test", fields={"n": 42})
        text = JSONFormatter().format(e)
        data = json.loads(text)
        assert data["level"] == "INFO"
        assert data["message"] == "test"

    def test_pretty(self):
        e = LogEntry.create(LogLevel.INFO, "x")
        text = JSONFormatter(indent=2).format(e)
        assert "\n" in text


class TestTextFormatter:
    def test_format_basic(self):
        e = LogEntry.create(LogLevel.WARNING, "watch out", tags=["db"])
        text = TextFormatter().format(e)
        assert "[WARNING]" in text
        assert "watch out" in text
        assert "db" in text

    def test_format_with_source_and_fields(self):
        e = LogEntry.create(LogLevel.INFO, "hi", fields={"uid": 1}, source="svc")
        text = TextFormatter().format(e)
        assert "src=svc" in text
        assert "uid=1" in text


class TestColoredFormatter:
    def test_includes_ansi(self):
        e = LogEntry.create(LogLevel.ERROR, "fail")
        text = ColoredFormatter().format(e)
        assert "\033[" in text  # has ANSI codes
        assert "ERROR" in text


# ── Handlers ──────────────────────────────────────────────────────────

class TestMemoryHandler:
    def test_captures_entries(self):
        h = MemoryHandler()
        e = LogEntry.create(LogLevel.INFO, "hi")
        h.emit(e)
        assert len(h.entries) == 1
        assert h.entries[0] is e

    def test_maxsize_trim(self):
        h = MemoryHandler(maxsize=3)
        for i in range(5):
            h.emit(LogEntry.create(LogLevel.INFO, str(i)))
        assert len(h.entries) == 3
        assert h.entries[0].message == "2"

    def test_clear(self):
        h = MemoryHandler()
        h.emit(LogEntry.create(LogLevel.INFO, "x"))
        h.clear()
        assert len(h.entries) == 0

    def test_get_entries_snapshot(self):
        h = MemoryHandler()
        h.emit(LogEntry.create(LogLevel.INFO, "a"))
        snap = h.get_entries()
        h.clear()
        assert len(snap) == 1  # snapshot survives clear


class TestCallbackHandler:
    def test_calls_callback(self):
        seen: list[LogEntry] = []
        h = CallbackHandler(callback=seen.append)
        e = LogEntry.create(LogLevel.INFO, "ping")
        h.emit(e)
        assert seen[0] is e


class TestConsoleHandler:
    def test_writes_to_stream(self):
        buf = io.StringIO()
        h = ConsoleHandler(stream=buf, formatter=TextFormatter())
        h.emit(LogEntry.create(LogLevel.INFO, "hello"))
        output = buf.getvalue()
        assert "hello" in output


class TestFileHandler:
    def test_appends_to_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.log"
            h = FileHandler(path, formatter=TextFormatter())
            h.emit(LogEntry.create(LogLevel.INFO, "line1"))
            h.emit(LogEntry.create(LogLevel.INFO, "line2"))
            content = path.read_text()
            assert "line1" in content
            assert "line2" in content

    def test_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sub" / "dir" / "log.txt"
            h = FileHandler(path, formatter=TextFormatter())
            h.emit(LogEntry.create(LogLevel.INFO, "deep"))
            assert path.exists()


# ── Filters ───────────────────────────────────────────────────────────

class TestLevelFilter:
    def test_passes_at_and_above(self):
        f = LevelFilter(LogLevel.WARNING)
        assert not f.matches(LogEntry.create(LogLevel.DEBUG, "x"))
        assert not f.matches(LogEntry.create(LogLevel.INFO, "x"))
        assert f.matches(LogEntry.create(LogLevel.WARNING, "x"))
        assert f.matches(LogEntry.create(LogLevel.ERROR, "x"))


class TestTagFilter:
    def test_any_mode(self):
        f = TagFilter(["api", "db"])
        assert f.matches(LogEntry.create(LogLevel.INFO, "x", tags=["api"]))
        assert f.matches(LogEntry.create(LogLevel.INFO, "x", tags=["db", "cache"]))
        assert not f.matches(LogEntry.create(LogLevel.INFO, "x", tags=["cache"]))

    def test_all_mode(self):
        f = TagFilter(["api", "db"], mode="all")
        assert f.matches(LogEntry.create(LogLevel.INFO, "x", tags=["api", "db"]))
        assert not f.matches(LogEntry.create(LogLevel.INFO, "x", tags=["api"]))

    def test_none_mode(self):
        f = TagFilter(["secret"], mode="none")
        assert f.matches(LogEntry.create(LogLevel.INFO, "x", tags=["public"]))
        assert not f.matches(LogEntry.create(LogLevel.INFO, "x", tags=["secret"]))

    def test_invalid_mode(self):
        with pytest.raises(ValueError):
            TagFilter(["x"], mode="bogus")


class TestFieldFilter:
    def test_required_fields(self):
        f = FieldFilter(required_fields={"user": "alice"})
        assert f.matches(LogEntry.create(LogLevel.INFO, "x", fields={"user": "alice", "ok": 1}))
        assert not f.matches(LogEntry.create(LogLevel.INFO, "x", fields={"user": "bob"}))
        assert not f.matches(LogEntry.create(LogLevel.INFO, "x", fields={}))

    def test_field_exists(self):
        f = FieldFilter(field_exists=["request_id"])
        assert f.matches(LogEntry.create(LogLevel.INFO, "x", fields={"request_id": "abc"}))
        assert not f.matches(LogEntry.create(LogLevel.INFO, "x", fields={}))


class TestPredicateFilter:
    def test_custom_predicate(self):
        f = PredicateFilter(lambda e: len(e.message) > 5)
        assert f.matches(LogEntry.create(LogLevel.INFO, "long message"))
        assert not f.matches(LogEntry.create(LogLevel.INFO, "short"))


class TestCompositeFilter:
    def test_and(self):
        f = CompositeFilter(
            LevelFilter(LogLevel.WARNING),
            TagFilter(["api"]),
            mode="and",
        )
        assert f.matches(LogEntry.create(LogLevel.ERROR, "x", tags=["api"]))
        assert not f.matches(LogEntry.create(LogLevel.ERROR, "x", tags=["db"]))
        assert not f.matches(LogEntry.create(LogLevel.DEBUG, "x", tags=["api"]))

    def test_or(self):
        f = CompositeFilter(
            TagFilter(["a"]),
            TagFilter(["b"]),
            mode="or",
        )
        assert f.matches(LogEntry.create(LogLevel.INFO, "x", tags=["a"]))
        assert f.matches(LogEntry.create(LogLevel.INFO, "x", tags=["b"]))
        assert not f.matches(LogEntry.create(LogLevel.INFO, "x", tags=["c"]))


# ── AppLogger ─────────────────────────────────────────────────────────

class TestAppLogger:
    def test_basic_log(self):
        mem = MemoryHandler()
        log = AppLogger("test", handlers=[mem])
        e = log.info("hello")
        assert len(mem.entries) == 1
        assert mem.entries[0].message == "hello"

    def test_all_levels(self):
        mem = MemoryHandler()
        log = AppLogger("test", handlers=[mem])
        log.trace("t")
        log.debug("d")
        log.info("i")
        log.warning("w")
        log.error("e")
        log.critical("c")
        assert len(mem.entries) == 6

    def test_level_filtering(self):
        mem = MemoryHandler()
        log = AppLogger("test", handlers=[mem], level=LogLevel.WARNING)
        log.info("hidden")
        log.warning("visible")
        log.error("also visible")
        assert len(mem.entries) == 2

    def test_fields_and_tags(self):
        mem = MemoryHandler()
        log = AppLogger("test", handlers=[mem])
        log.info("req", fields={"path": "/api"}, tags=["http"])
        e = mem.entries[0]
        assert e.fields["path"] == "/api"
        assert "http" in e.tags

    def test_context(self):
        mem = MemoryHandler()
        log = AppLogger("test", handlers=[mem])
        with log.context(request_id="r1"):
            log.info("inside")
        log.info("outside")
        assert mem.entries[0].fields["request_id"] == "r1"
        assert "request_id" not in mem.entries[1].fields

    def test_nested_context(self):
        mem = MemoryHandler()
        log = AppLogger("test", handlers=[mem])
        with log.context(a=1):
            with log.context(b=2):
                log.info("deep")
        assert mem.entries[0].fields == {"a": 1, "b": 2}

    def test_default_tags(self):
        mem = MemoryHandler()
        log = AppLogger("test", handlers=[mem], default_tags=["app"])
        log.info("hi", tags=["extra"])
        assert "app" in mem.entries[0].tags
        assert "extra" in mem.entries[0].tags

    def test_filter_on_logger(self):
        mem = MemoryHandler()
        log = AppLogger("test", handlers=[mem])
        log.add_filter(TagFilter(["important"]))
        log.info("normal", tags=["normal"])
        log.info("important", tags=["important"])
        assert len(mem.entries) == 1
        assert mem.entries[0].message == "important"

    def test_handler_management(self):
        mem1 = MemoryHandler()
        mem2 = MemoryHandler()
        log = AppLogger("test", handlers=[mem1])
        log.add_handler(mem2)
        log.info("both")
        assert len(mem1.entries) == 1
        assert len(mem2.entries) == 1
        log.remove_handler(mem1)
        log.info("only mem2")
        assert len(mem1.entries) == 1
        assert len(mem2.entries) == 2

    def test_source_is_logger_name(self):
        mem = MemoryHandler()
        log = AppLogger("myservice", handlers=[mem])
        log.info("test")
        assert mem.entries[0].source == "myservice"

    def test_log_returns_entry(self):
        log = AppLogger("test", handlers=[MemoryHandler()])
        e = log.info("hello", fields={"k": "v"})
        assert isinstance(e, LogEntry)
        assert e.fields["k"] == "v"
