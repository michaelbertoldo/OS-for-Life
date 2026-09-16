"""Field-ownership merge, reconcile, done_at cleanup, snooze reset (spec §3-4)."""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import frontmatter

from lifeos.engine import vault
from lifeos.engine.state import State
from lifeos.models import Item

TZ = ZoneInfo("America/Denver")
NOW = datetime(2026, 9, 16, 15, 0, tzinfo=TZ)


def make_item(**overrides) -> Item:
    defaults = dict(domain="school", type="assignment", source="canvas", title="t", uid="u1")
    defaults.update(overrides)
    return Item(**defaults)


def test_python_owns_everything_but_status_on_synced_items(tmp_path):
    state = State()
    item = make_item(title="Original title", status="open")
    vault.merge_item(tmp_path, item, state, NOW)

    path = vault.item_note_path(tmp_path, "u1")
    post = frontmatter.load(path)
    post.metadata["status"] = "snoozed"  # Michael snoozes it in Obsidian
    path.write_bytes(frontmatter.dumps(post).encode("utf-8"))

    updated = make_item(title="New title from source", status="open")
    vault.merge_item(tmp_path, updated, state, NOW)

    post = frontmatter.load(path)
    assert post.metadata["title"] == "New title from source"  # Python overwrote it
    assert post.metadata["status"] == "snoozed"  # but not status


def test_collector_reported_done_moves_status_and_records_done_at(tmp_path):
    state = State()
    vault.merge_item(tmp_path, make_item(status="open"), state, NOW)

    submitted = make_item(status="done")
    result = vault.merge_item(tmp_path, submitted, state, NOW)

    assert result.status == "done"
    assert "u1" in state.done_at


def test_reconcile_deletes_open_item_no_longer_returned(tmp_path):
    state = State()
    vault.merge_item(tmp_path, make_item(uid="gone", source="gmail", type="email", status="open"), state, NOW)
    removed = vault.reconcile_source(tmp_path, "gmail", current_uids=set(), now=NOW)
    assert removed == ["gone"]
    assert not vault.item_note_path(tmp_path, "gone").exists()


def test_reconcile_never_removes_learning_suite_items(tmp_path):
    state = State()
    vault.merge_item(tmp_path, make_item(uid="ls1", source="learning-suite", status="open"), state, NOW)
    removed = vault.reconcile_source(tmp_path, "learning-suite", current_uids=set(), now=NOW)
    assert removed == []
    assert vault.item_note_path(tmp_path, "ls1").exists()


def test_reconcile_keeps_past_due_canvas_items(tmp_path):
    state = State()
    item = make_item(uid="c1", source="canvas", status="open", due=NOW - timedelta(days=1))
    vault.merge_item(tmp_path, item, state, NOW)
    removed = vault.reconcile_source(tmp_path, "canvas", current_uids=set(), now=NOW)
    assert removed == []
    assert vault.item_note_path(tmp_path, "c1").exists()


def test_cleanup_ended_events_removes_past_events_regardless_of_source(tmp_path):
    state = State()
    item = make_item(uid="ev1", source="gcal", type="event", status="open", due=NOW - timedelta(hours=1))
    vault.merge_item(tmp_path, item, state, NOW)
    removed = vault.cleanup_ended_events(tmp_path, NOW)
    assert removed == ["ev1"]
    assert not vault.item_note_path(tmp_path, "ev1").exists()


def test_reset_snoozed_only_runs_once_per_day(tmp_path):
    state = State()
    vault.merge_item(tmp_path, make_item(uid="s1", status="open"), state, NOW)
    path = vault.item_note_path(tmp_path, "s1")
    post = frontmatter.load(path)
    post.metadata["status"] = "snoozed"  # Michael snoozes it in Obsidian
    path.write_bytes(frontmatter.dumps(post).encode("utf-8"))

    count = vault.reset_snoozed(tmp_path, state, "2026-09-16")
    assert count == 1
    post = frontmatter.load(vault.item_note_path(tmp_path, "s1"))
    assert post.metadata["status"] == "open"

    post.metadata["status"] = "snoozed"
    vault.item_note_path(tmp_path, "s1").write_bytes(frontmatter.dumps(post).encode("utf-8"))
    count_again = vault.reset_snoozed(tmp_path, state, "2026-09-16")
    assert count_again == 0  # already ran today


def test_prune_done_deletes_after_14_days(tmp_path):
    state = State()
    vault.merge_item(tmp_path, make_item(uid="d1", status="open"), state, NOW)
    vault.merge_item(tmp_path, make_item(uid="d1", status="done"), state, NOW)
    assert "d1" in state.done_at

    removed_early = vault.prune_done(tmp_path, state, NOW + timedelta(days=13))
    assert removed_early == []
    assert vault.item_note_path(tmp_path, "d1").exists()

    removed_late = vault.prune_done(tmp_path, state, NOW + timedelta(days=15))
    assert removed_late == ["d1"]
    assert not vault.item_note_path(tmp_path, "d1").exists()
    assert "d1" not in state.done_at
