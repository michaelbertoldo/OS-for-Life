"""state.json: last success/error per source, done_at dates, last sync date (spec §2, §4)."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

DEFAULT_STATE_PATH = Path.home() / ".local" / "state" / "lifeos" / "state.json"


class SourceState(BaseModel):
    last_success: str | None = None
    last_error: str | None = None
    last_error_message: str | None = None
    failing_since: str | None = None  # set when a source first fails; cleared on success


class State(BaseModel):
    sources: dict[str, SourceState] = Field(default_factory=dict)
    done_at: dict[str, str] = Field(default_factory=dict)
    last_sync_date: str | None = None


def load_state(path: Path | None = None) -> State:
    path = path or DEFAULT_STATE_PATH
    if not path.exists():
        return State()
    return State.model_validate_json(path.read_text())


def save_state(state: State, path: Path | None = None) -> None:
    path = path or DEFAULT_STATE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(state.model_dump_json(indent=2))


def record_success(state: State, source: str, now: datetime) -> None:
    s = state.sources.setdefault(source, SourceState())
    s.last_success = now.isoformat()
    s.last_error = None
    s.last_error_message = None
    s.failing_since = None


def record_error(state: State, source: str, now: datetime, message: str) -> None:
    s = state.sources.setdefault(source, SourceState())
    s.last_error = now.isoformat()
    s.last_error_message = message
    if s.failing_since is None:
        s.failing_since = now.isoformat()


def hours_failing(state: State, source: str, now: datetime) -> float | None:
    """How long ``source`` has been continuously failing, or None if it's healthy."""
    s = state.sources.get(source)
    if not s or not s.failing_since:
        return None
    since = datetime.fromisoformat(s.failing_since)
    return (now - since).total_seconds() / 3600
