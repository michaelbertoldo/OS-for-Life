"""Course notes in 10 School/<course>/ (spec §5.1, §5.2, §8).

Python owns only grade, letter, and grade_updated on these notes — never the
rest of the note, which may have other content Michael added.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import frontmatter

_SAFE_NAME = re.compile(r"[^A-Za-z0-9 _.-]")


def _safe_course_dirname(course: str) -> str:
    return _SAFE_NAME.sub("_", course).strip() or "Unknown Course"


def course_note_path(vault_path: Path, course: str) -> Path:
    dirname = _safe_course_dirname(course)
    return vault_path / "10 School" / dirname / f"{dirname}.md"


def update_course_grade(
    vault_path: Path,
    course: str,
    platform: str,
    grade: float | None,
    letter: str | None,
    now: datetime,
) -> Path:
    path = course_note_path(vault_path, course)
    if path.exists():
        post = frontmatter.load(path)
    else:
        post = frontmatter.Post("")
        post.metadata = {"course": course}
        path.parent.mkdir(parents=True, exist_ok=True)

    post.metadata["platform"] = platform
    post.metadata["grade"] = grade
    post.metadata["letter"] = "hidden" if (grade is None and letter is None) else letter
    post.metadata["grade_updated"] = now.isoformat()

    path.write_bytes(frontmatter.dumps(post).encode("utf-8"))
    return path


def ensure_course_note(vault_path: Path, course: str, platform: str) -> Path:
    """Create an empty course note (no grade) if one doesn't exist yet. Never overwrites."""
    path = course_note_path(vault_path, course)
    if path.exists():
        return path
    post = frontmatter.Post("")
    post.metadata = {"course": course, "platform": platform, "grade": None, "letter": None, "grade_updated": None}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(frontmatter.dumps(post).encode("utf-8"))
    return path
