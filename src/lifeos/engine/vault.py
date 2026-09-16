"""Vault writer: field-ownership merge, reconcile, done_at cleanup, snooze reset (spec §3-4).

Only touches ``90 Sync/`` here. Course notes, snapshot.md, and sync-status.md
are written by other modules.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import frontmatter

from lifeos.engine.state import State
from lifeos.models import Item

SYNC_DIR = "90 Sync"
DONE_RETENTION_DAYS = 14


def sync_dir(vault_path: Path) -> Path:
    return vault_path / SYNC_DIR


def item_note_path(vault_path: Path, uid: str) -> Path:
    return sync_dir(vault_path) / f"{uid}.md"


def _item_properties(item: Item) -> dict:
    """Core + context properties, as they should be written to frontmatter."""
    return item.model_dump(mode="json", exclude_none=True)


def merge_item(vault_path: Path, item: Item, state: State, now: datetime) -> Item:
    """Write one synced item into 90 Sync/, respecting field ownership.

    Python owns every property except ``status``, which Michael owns from the
    note. The one exception: a collector may report ``status="done"`` (e.g. a
    Canvas submission) and that's allowed to move an open/snoozed item to
    done. Returns the item as actually persisted (with the resolved status).
    """
    path = item_note_path(vault_path, item.uid)
    existing_status = None
    if path.exists():
        post = frontmatter.load(path)
        existing_status = post.metadata.get("status")

    resolved_status = existing_status or "open"
    became_done = False
    if item.status == "done" and resolved_status != "done":
        resolved_status = "done"
        became_done = True
    persisted = item.model_copy(update={"status": resolved_status})

    post = frontmatter.Post("")
    post.metadata = _item_properties(persisted)
    sync_dir(vault_path).mkdir(parents=True, exist_ok=True)
    path.write_bytes(frontmatter.dumps(post).encode("utf-8"))

    if became_done:
        state.done_at[item.uid] = now.isoformat()

    return persisted


def reconcile_source(vault_path: Path, source: str, current_uids: set[str], now: datetime) -> list[str]:
    """Delete open notes for ``source`` that the latest sync no longer returned.

    Exceptions (never deleted here): learning-suite items, and past-due
    Canvas items (they wait for submission or a manual "done").
    Returns the uids removed.
    """
    removed: list[str] = []
    if source == "learning-suite":
        return removed

    d = sync_dir(vault_path)
    if not d.exists():
        return removed

    for path in d.glob("*.md"):
        post = frontmatter.load(path)
        meta = post.metadata
        if meta.get("source") != source:
            continue
        uid = meta.get("uid")
        if uid in current_uids:
            continue
        if meta.get("status") != "open":
            continue
        if source == "canvas":
            due = meta.get("due")
            if due and _parse_dt(due) < now:
                continue  # past-due Canvas items stay until submitted/done
        path.unlink()
        removed.append(uid)
    return removed


def cleanup_ended_events(vault_path: Path, now: datetime) -> list[str]:
    """Events are deleted once they end, regardless of source or status."""
    removed: list[str] = []
    d = sync_dir(vault_path)
    if not d.exists():
        return removed
    for path in d.glob("*.md"):
        post = frontmatter.load(path)
        meta = post.metadata
        if meta.get("type") != "event":
            continue
        due = meta.get("due")
        if due and _parse_dt(due) < now:
            path.unlink()
            removed.append(meta.get("uid"))
    return removed


def reset_snoozed(vault_path: Path, state: State, today: str) -> int:
    """First sync after midnight: snoozed -> open. ``today`` is 'YYYY-MM-DD'."""
    if state.last_sync_date == today:
        return 0
    count = 0
    d = sync_dir(vault_path)
    if d.exists():
        for path in d.glob("*.md"):
            post = frontmatter.load(path)
            if post.metadata.get("status") == "snoozed":
                post.metadata["status"] = "open"
                path.write_bytes(frontmatter.dumps(post).encode("utf-8"))
                count += 1
    state.last_sync_date = today
    return count


def prune_done(vault_path: Path, state: State, now: datetime) -> list[str]:
    """Delete notes 14 days after they were marked done."""
    removed: list[str] = []
    d = sync_dir(vault_path)
    for uid, done_at_iso in list(state.done_at.items()):
        done_at = _parse_dt(done_at_iso)
        if now - done_at < timedelta(days=DONE_RETENTION_DAYS):
            continue
        path = d / f"{uid}.md"
        if path.exists():
            path.unlink()
        removed.append(uid)
        del state.done_at[uid]
    return removed


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)
