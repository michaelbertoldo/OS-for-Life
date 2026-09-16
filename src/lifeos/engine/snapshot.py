"""Writes 00 Home/snapshot.md every sync (spec §10). Plain markdown, ~150 lines max."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import frontmatter

from lifeos.engine.state import State

SNAPSHOT_MAX_LINES = 150
AGENDA_LIMIT = 20
MISSING_LIMIT = 15
DUE_SOON_LIMIT = 15


def _read_sync_items(vault_path: Path) -> list[dict]:
    d = vault_path / "90 Sync"
    if not d.exists():
        return []
    return [frontmatter.load(p).metadata for p in d.glob("*.md")]


def _read_course_notes(vault_path: Path) -> list[dict]:
    d = vault_path / "10 School"
    if not d.exists():
        return []
    return [frontmatter.load(p).metadata for p in d.glob("*/*.md")]


def _parse_dt(value) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def write_snapshot(vault_path: Path, state: State, now: datetime, habit_streaks: dict[str, int]) -> Path:
    items = _read_sync_items(vault_path)
    open_items = [i for i in items if i.get("status") == "open"]
    tomorrow_end = (now + timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    agenda = sorted(
        (i for i in open_items if (d := _parse_dt(i.get("due"))) and today_start <= d < tomorrow_end),
        key=lambda i: _parse_dt(i["due"]),
    )[:AGENDA_LIMIT]
    top10 = sorted(open_items, key=lambda i: -(i.get("score") or 0))[:10]

    all_missing = sorted(
        (i for i in open_items if i.get("source") in ("canvas", "learning-suite")
         and (d := _parse_dt(i.get("due"))) and d < now),
        key=lambda i: _parse_dt(i["due"]),
    )
    missing = all_missing[:MISSING_LIMIT]
    week_end = now + timedelta(days=7)
    due_soon = sorted(
        (i for i in open_items if i.get("domain") == "school"
         and (d := _parse_dt(i.get("due"))) and now <= d < week_end),
        key=lambda i: _parse_dt(i["due"]),
    )[:DUE_SOON_LIMIT]

    grades = _read_course_notes(vault_path)

    lines = [
        f"# Snapshot — {now.isoformat()}",
        "",
        "## Sync status",
    ]
    if not state.sources:
        lines.append("- (no syncs recorded yet)")
    for source in sorted(state.sources):
        s = state.sources[source]
        status = "ok" if s.last_success and not s.last_error else "FAILING"
        lines.append(f"- {source}: {status} (last success: {s.last_success or 'never'})")

    lines += ["", "## Agenda (today & tomorrow)"]
    if not agenda:
        lines.append("- nothing due")
    for i in agenda:
        lines.append(f"- [{i.get('due')}] {i.get('title')} ({i.get('domain')})")

    lines += ["", "## Top 10"]
    for i in top10:
        lines.append(f"- {i.get('title')} — {i.get('domain')}, due {i.get('due') or '-'}, score {i.get('score')} — {i.get('link') or ''}")

    lines += ["", "## School"]
    lines.append(f"### Missing ({len(all_missing)})")
    for i in missing:
        lines.append(f"- {i.get('title')} ({i.get('course') or ''}) — due {i.get('due')}")
    lines.append("### Due in 7 days")
    for i in due_soon:
        lines.append(f"- {i.get('title')} ({i.get('course') or ''}) — due {i.get('due')}")
    grade_line = " · ".join(
        f"{g.get('course')}: {g.get('grade') if g.get('grade') is not None else g.get('letter')}"
        for g in sorted(grades, key=lambda g: g.get("course") or "")
    )
    lines.append(f"### Grades: {grade_line or '(none yet)'}")

    lines += ["", "## Habit streaks"]
    if not habit_streaks:
        lines.append("- (no habits configured yet)")
    for habit, streak in habit_streaks.items():
        lines.append(f"- {habit}: {streak}")

    text = "\n".join(lines[:SNAPSHOT_MAX_LINES]) + "\n"
    path = vault_path / "00 Home" / "snapshot.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path
