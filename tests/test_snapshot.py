"""snapshot.md: agenda, top 10, school section, habit streaks, stays under the line cap (spec §10)."""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from lifeos.engine import vault
from lifeos.engine.course_notes import update_course_grade
from lifeos.engine.snapshot import SNAPSHOT_MAX_LINES, write_snapshot
from lifeos.engine.state import State, record_success
from lifeos.models import Item

TZ = ZoneInfo("America/Denver")
NOW = datetime(2026, 9, 16, 15, 0, tzinfo=TZ)


def make_item(**overrides):
    defaults = dict(domain="school", type="assignment", source="canvas", title="t", uid="u1", status="open")
    defaults.update(overrides)
    return Item(**defaults)


def test_snapshot_includes_agenda_top10_school_and_habits(tmp_path):
    state = State()
    record_success(state, "canvas", NOW)

    vault.merge_item(tmp_path, make_item(uid="due-tomorrow", due=NOW + timedelta(hours=20), score=80), state, NOW)
    vault.merge_item(tmp_path, make_item(uid="overdue", due=NOW - timedelta(hours=5), score=90, source="canvas"), state, NOW)
    update_course_grade(tmp_path, "IS 401", "canvas", 94.5, "A", NOW)

    path = write_snapshot(tmp_path, state, NOW, habit_streaks={"workout": 3})
    text = path.read_text()

    assert "canvas: ok" in text
    assert "due-tomorrow" not in text  # uid isn't shown, title is
    assert "Missing (1)" in text
    assert "IS 401: 94.5" in text
    assert "workout: 3" in text
    assert len(text.splitlines()) <= SNAPSHOT_MAX_LINES


def test_snapshot_stays_under_line_cap_with_many_items(tmp_path):
    state = State()
    for n in range(60):
        vault.merge_item(tmp_path, make_item(uid=f"item-{n}", due=NOW + timedelta(hours=n), score=float(n)), state, NOW)
    path = write_snapshot(tmp_path, state, NOW, habit_streaks={})
    assert len(path.read_text().splitlines()) <= SNAPSHOT_MAX_LINES
