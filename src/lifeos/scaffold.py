"""Scaffolds the vault once (spec §3, §9, §10, P0-09). Never overwrites a file that exists."""
from __future__ import annotations

import json
from pathlib import Path

VAULT_DIRS = [
    "00 Home",
    "10 School",
    "20 Mentors",
    "30 Ventures/Spiced",
    "30 Ventures/Javvas",
    "40 Me/goals",
    "50 Journal",
    "90 Sync",
    "_templates",
]

TAB_PLACEHOLDER = """\
_Placeholder — the Bases views for this tab are built in a later phase, per docs/SPEC.md §8._
"""

VAULT_CLAUDE_MD = """\
# LifeOS

## Who Michael is
See [[about-me]] (`40 Me/about-me.md`).

## Vault map
- `00 Home/` — the six tabs (Today, School, Mentors, Ventures, Inbox, Brain), snapshot.md, sync-status.md
- `10 School/` — one folder per course
- `20 Mentors/` — Mentors International
- `30 Ventures/` — Spiced/, Javvas/
- `40 Me/` — about-me.md, habits.md, goals/, weekly reviews
- `50 Journal/` — daily notes (habit tracking)
- `90 Sync/` — synced items, one note per item. Don't edit these except `status`.
- `_templates/` — task.md, goal.md, weekly-review.md

## Start here
For what matters now, read `00 Home/snapshot.md` first.

## Priority order
School, then Mentors International, then Spiced and Javvas.

## Rules
- Don't edit notes in `90 Sync/` except the `status` field.
- Create new tasks from `_templates/task.md`.
- Don't copy vault content outside the vault without asking.
"""

ABOUT_ME_STUB = """\
---
---
# About me

_Michael fills this in (spec §10, task P4-05)._
"""

HABITS_STUB = """\
<!-- One habit per line, about 5 max, e.g.: -->
<!-- - read scripture -->
<!-- - workout -->
"""

TASK_TEMPLATE = """\
---
domain: other
type: task
due:
status: open
source: manual
link:
title: {{title}}
uid: manual-{{title}}
goal:
---

"""

GOAL_TEMPLATE = """\
---
level: week
parent:
status: active
---

# {{title}}
"""

WEEKLY_REVIEW_TEMPLATE = """\
# Weekly review — {{date}}

## Wins

## School

## Ventures

## Habits

## Next week
"""


def _write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return True


def replace_placeholder_tab(vault_path: Path, tab: str, content: str) -> bool:
    """Replace a tab note's content, but only if it still holds the P0-09 placeholder —
    never overwrites something Michael wrote in Obsidian since. Returns whether it wrote."""
    path = vault_path / "00 Home" / f"{tab}.md"
    placeholder = f"# {tab}\n\n{TAB_PLACEHOLDER}"
    if path.exists() and path.read_text() != placeholder:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return True


def scaffold_vault(vault_path: Path) -> list[Path]:
    """Create the vault structure. Returns the paths actually created."""
    created: list[Path] = []

    for d in VAULT_DIRS:
        (vault_path / d).mkdir(parents=True, exist_ok=True)

    tabs = ["Today", "School", "Mentors", "Ventures", "Inbox", "Brain"]
    for tab in tabs:
        p = vault_path / "00 Home" / f"{tab}.md"
        if _write_if_missing(p, f"# {tab}\n\n{TAB_PLACEHOLDER}"):
            created.append(p)

    for name, content in [
        ("CLAUDE.md", VAULT_CLAUDE_MD),
        ("40 Me/about-me.md", ABOUT_ME_STUB),
        ("40 Me/habits.md", HABITS_STUB),
        ("_templates/task.md", TASK_TEMPLATE),
        ("_templates/goal.md", GOAL_TEMPLATE),
        ("_templates/weekly-review.md", WEEKLY_REVIEW_TEMPLATE),
    ]:
        p = vault_path / name
        if _write_if_missing(p, content):
            created.append(p)

    agents_path = vault_path / "AGENTS.md"
    if not agents_path.exists() and not agents_path.is_symlink():
        agents_path.symlink_to("CLAUDE.md")
        created.append(agents_path)

    if register_property_types(vault_path):
        created.append(vault_path / ".obsidian" / "types.json")

    return created


# Obsidian's Properties view stores per-property types in .obsidian/types.json.
# This location and format aren't in the official docs (verified 2026-09-16;
# see PROGRESS.md -> Decisions), so this is best-effort: it merges in the
# types the spec cares about without touching anything already set, and Gate 0
# double-checks in the Obsidian UI that due/score render as date/number.
PROPERTY_TYPES = {
    "due": "datetime",
    "received": "datetime",
    "score": "number",
    "grade": "number",
}


def register_property_types(vault_path: Path) -> bool:
    return register_property_type_map(vault_path, PROPERTY_TYPES)


def register_property_type(vault_path: Path, prop: str, type_name: str) -> bool:
    return register_property_type_map(vault_path, {prop: type_name})


def register_property_type_map(vault_path: Path, types: dict[str, str]) -> bool:
    path = vault_path / ".obsidian" / "types.json"
    data = {"types": {}}
    if path.exists():
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return False
    data.setdefault("types", {})
    changed = False
    for prop, type_name in types.items():
        if prop not in data["types"]:
            data["types"][prop] = type_name
            changed = True
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
    return changed
