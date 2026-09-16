"""Habits (spec §9). habits.md is Michael's list; daily notes track checkboxes; streaks
are computed for snapshot.md only — habits never affect score.
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path

import frontmatter

from lifeos.scaffold import register_property_type

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(habit: str) -> str:
    return _SLUG_RE.sub("-", habit.strip().lower()).strip("-")


def read_habits(vault_path: Path) -> list[str]:
    path = vault_path / "40 Me" / "habits.md"
    if not path.exists():
        return []
    habits = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            habits.append(stripped[2:].strip())
    return habits


def daily_note_path(vault_path: Path, day: date) -> Path:
    return vault_path / "50 Journal" / f"{day.isoformat()}.md"


def ensure_daily_note(vault_path: Path, today: date, habits: list[str]) -> Path:
    """Create today's note if missing. Only today's note may gain a newly added
    habit property; past notes are never modified."""
    path = daily_note_path(vault_path, today)
    slugs = {slugify(h): h for h in habits}

    if path.exists():
        post = frontmatter.load(path)
    else:
        post = frontmatter.Post("")
        post.metadata = {"date": today.isoformat()}
        path.parent.mkdir(parents=True, exist_ok=True)
        register_property_type(vault_path, "date", "date")

    changed = not path.exists()
    for slug in slugs:
        if slug not in post.metadata:
            post.metadata[slug] = False
            changed = True
            register_property_type(vault_path, slug, "checkbox")

    if changed:
        path.write_bytes(frontmatter.dumps(post).encode("utf-8"))
    return path


def compute_streaks(vault_path: Path, today: date, habits: list[str]) -> dict[str, int]:
    """Consecutive checked days through yesterday, plus today if checked."""
    streaks: dict[str, int] = {}
    for habit in habits:
        slug = slugify(habit)
        count = 0
        day = today
        checked_today = _is_checked(vault_path, today, slug)
        if checked_today:
            count += 1
        day = today - timedelta(days=1)
        while _is_checked(vault_path, day, slug):
            count += 1
            day -= timedelta(days=1)
        streaks[habit] = count
    return streaks


def _is_checked(vault_path: Path, day: date, slug: str) -> bool:
    path = daily_note_path(vault_path, day)
    if not path.exists():
        return False
    post = frontmatter.load(path)
    return bool(post.metadata.get(slug, False))
