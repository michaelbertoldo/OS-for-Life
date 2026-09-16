"""Habits: daily note creation, only today gains new habit properties, streaks (spec §9)."""
from __future__ import annotations

from datetime import date

import frontmatter

from lifeos.engine import habits


def write_habits_md(vault_path, lines):
    path = vault_path / "40 Me" / "habits.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"- {h}" for h in lines) + "\n")


def test_read_habits_parses_list_lines(tmp_path):
    write_habits_md(tmp_path, ["read scripture", "workout"])
    assert habits.read_habits(tmp_path) == ["read scripture", "workout"]


def test_ensure_daily_note_creates_with_unchecked_habits(tmp_path):
    today = date(2026, 9, 16)
    path = habits.ensure_daily_note(tmp_path, today, ["read scripture", "workout"])
    post = frontmatter.load(path)
    assert post.metadata["date"] == "2026-09-16"
    assert post.metadata["read-scripture"] is False
    assert post.metadata["workout"] is False


def test_only_todays_note_gains_a_newly_added_habit(tmp_path):
    today = date(2026, 9, 16)
    yesterday = date(2026, 9, 15)
    habits.ensure_daily_note(tmp_path, yesterday, ["workout"])
    habits.ensure_daily_note(tmp_path, today, ["workout", "read scripture"])

    today_post = frontmatter.load(habits.daily_note_path(tmp_path, today))
    assert "read-scripture" in today_post.metadata

    yesterday_post = frontmatter.load(habits.daily_note_path(tmp_path, yesterday))
    assert "read-scripture" not in yesterday_post.metadata  # past notes untouched


def test_ensure_daily_note_never_resets_an_existing_checked_value(tmp_path):
    today = date(2026, 9, 16)
    path = habits.ensure_daily_note(tmp_path, today, ["workout"])
    post = frontmatter.load(path)
    post.metadata["workout"] = True
    path.write_bytes(frontmatter.dumps(post).encode("utf-8"))

    habits.ensure_daily_note(tmp_path, today, ["workout", "read scripture"])
    post = frontmatter.load(path)
    assert post.metadata["workout"] is True


def test_streak_counts_consecutive_checked_days_including_today(tmp_path):
    for day, checked in [
        (date(2026, 9, 14), True),
        (date(2026, 9, 15), True),
        (date(2026, 9, 16), True),
    ]:
        path = habits.ensure_daily_note(tmp_path, day, ["workout"])
        post = frontmatter.load(path)
        post.metadata["workout"] = checked
        path.write_bytes(frontmatter.dumps(post).encode("utf-8"))

    streaks = habits.compute_streaks(tmp_path, date(2026, 9, 16), ["workout"])
    assert streaks["workout"] == 3


def test_streak_stops_at_first_unchecked_day(tmp_path):
    days = {
        date(2026, 9, 13): False,
        date(2026, 9, 14): True,
        date(2026, 9, 15): True,
        date(2026, 9, 16): True,
    }
    for day, checked in days.items():
        path = habits.ensure_daily_note(tmp_path, day, ["workout"])
        post = frontmatter.load(path)
        post.metadata["workout"] = checked
        path.write_bytes(frontmatter.dumps(post).encode("utf-8"))

    streaks = habits.compute_streaks(tmp_path, date(2026, 9, 16), ["workout"])
    assert streaks["workout"] == 3  # 14th-16th checked; the 13th (unchecked) stops the walk
