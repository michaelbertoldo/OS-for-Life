"""Writes .base files (Obsidian Bases YAML). Verified against the current official docs
(help.obsidian.md/bases, fetched 2026-09-16) before writing anything here — see
docs/SPEC.md rule 6 and the Decisions log in PROGRESS.md for what's confirmed vs. best-effort.
"""
from __future__ import annotations

from pathlib import Path

# Row sort isn't shown in the official schema example (only `groupBy` and
# column `order` are documented). This follows the same {property, direction}
# shape as the documented `groupBy` key, since the UI describes sort as a list
# of properties with priority order. Verify in Obsidian's Sort menu once the
# fixture data loads (P0-11) — if the UI writes a different key, fix this and
# log it in PROGRESS.md -> Decisions.
FIXTURE_TEST_BASE_YAML = """\
filters:
  and:
    - source == "fixture"
views:
  - type: table
    name: "Fixture test"
    order:
      - title
      - domain
      - type
      - due
      - score
      - status
      - link
    sort:
      - property: score
        direction: DESC
"""


def write_base_file(vault_path: Path, relative_path: str, yaml_content: str, overwrite: bool = False) -> Path:
    path = vault_path / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    if overwrite or not path.exists():
        path.write_text(yaml_content)
    return path


# Today.md (spec §8): Agenda (events + anything due today/tomorrow) and Top 7
# (open, non-event, highest score) are scoped to 90 Sync/ via the global
# filter, since course notes elsewhere in the vault shouldn't leak in. Habits
# scans 50 Journal/ instead, so it carries its own file.folder filter.
#
# The Habits view's columns are generated from habits.md (P1-14/P1-15) rather
# than hardcoded, since habit names are Michael's own list. Re-run
# today_base_yaml() and rewrite this file whenever habits.md changes.
def today_base_yaml(habit_slugs: list[str]) -> str:
    habit_columns = "\n".join(f"      - {slug}" for slug in habit_slugs)
    return f"""\
filters:
  and:
    - file.folder == "90 Sync"
views:
  - type: table
    name: "Agenda"
    filters:
      and:
        - status == "open"
        - due != null
        - due >= today()
        - due < (today() + "2d")
    order:
      - due
      - title
      - domain
    sort:
      - property: due
        direction: ASC
  - type: table
    name: "Top 7"
    filters:
      and:
        - status == "open"
        - type != "event"
    limit: 7
    order:
      - title
      - domain
      - due
      - score
      - status
      - link
    sort:
      - property: score
        direction: DESC
  - type: table
    name: "Habits"
    filters:
      and:
        - file.folder == "50 Journal"
    limit: 7
    order:
      - date
{habit_columns}
    sort:
      - property: date
        direction: DESC
"""

# School.md (spec §8): each view scopes its own file.folder, since "Grades"
# reads course notes in 10 School/ rather than synced items in 90 Sync/.
SCHOOL_BASE_YAML = """\
views:
  - type: table
    name: "Due in next 14 days"
    filters:
      and:
        - file.folder == "90 Sync"
        - domain == "school"
        - status == "open"
        - due != null
        - due < (today() + "14d")
    groupBy:
      property: course
      direction: ASC
    order:
      - title
      - due
      - score
      - status
      - platform
      - link
    sort:
      - property: due
        direction: ASC
  - type: table
    name: "Missing"
    filters:
      and:
        - file.folder == "90 Sync"
        - status == "open"
        - due != null
        - due < now()
        - or:
            - source == "canvas"
            - source == "learning-suite"
    order:
      - title
      - course
      - due
      - status
      - link
    sort:
      - property: due
        direction: ASC
  - type: table
    name: "Grades"
    filters:
      and:
        - file.folder.startsWith("10 School")
    order:
      - course
      - platform
      - grade
      - letter
      - grade_updated
    sort:
      - property: course
        direction: ASC
  - type: table
    name: "Announcements and messages"
    filters:
      and:
        - file.folder == "90 Sync"
        - domain == "school"
        - status == "open"
        - or:
            - type == "announcement"
            - type == "message"
    order:
      - title
      - course
      - received
      - link
    sort:
      - property: received
        direction: DESC
"""
