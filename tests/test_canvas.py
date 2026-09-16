"""Canvas collector, entirely against saved fixtures via httpx.MockTransport. No network."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pytest

from lifeos.collectors import canvas
from lifeos.config import Config

FIXTURES = Path(__file__).parent / "fixtures" / "canvas"
NOW = datetime(2026, 9, 16, 15, 0, tzinfo=ZoneInfo("America/Denver"))


def _load(name: str):
    return json.loads((FIXTURES / f"{name}.json").read_text())


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/api/v1/courses":
        return httpx.Response(200, json=_load("courses"))
    if path == "/api/v1/users/self/enrollments":
        return httpx.Response(200, json=_load("enrollments"))
    if path == "/api/v1/planner/items":
        return httpx.Response(200, json=_load("planner_items"))
    if path == "/api/v1/users/self/missing_submissions":
        return httpx.Response(200, json=_load("missing_submissions"))
    if path == "/api/v1/announcements":
        return httpx.Response(200, json=_load("announcements"))
    if path == "/api/v1/conversations":
        return httpx.Response(200, json=_load("conversations"))
    if path == "/api/v1/calendar_events":
        return httpx.Response(200, json=_load("teacher_calendar_events"))
    if path == "/api/v1/courses/2001/assignments":
        return httpx.Response(200, json=_load("teacher_assignments"))
    raise AssertionError(f"unexpected request: {path}")


@pytest.fixture
def client():
    return httpx.Client(base_url="https://byu.instructure.com", transport=httpx.MockTransport(_handler))


def test_collect_never_touches_the_network_and_parses_all_item_types(client):
    config = Config(canvas_base_url="https://byu.instructure.com")
    items = canvas.collect(config, client=client, now=NOW)
    by_uid = {i.uid: i for i in items}

    assignment = by_uid["canvas-assignment-5001"]
    assert assignment.type == "assignment" and assignment.status == "open" and assignment.course == "IS 401"

    exam = by_uid["canvas-assignment-5002"]
    assert exam.type == "exam" and exam.status == "done" and exam.is_major  # graded + points >= threshold

    missing = by_uid["canvas-assignment-5003"]
    assert missing.status == "open" and missing.course == "FIN 201"

    announcement = by_uid["canvas-announcement-6001"]
    assert announcement.type == "announcement" and "6002" not in by_uid  # read one excluded

    message = by_uid["canvas-message-7001"]
    assert message.type == "message" and message.title == "Question about extension"

    teaching_event = by_uid["canvas-event-8001"]
    assert teaching_event.domain == "mentors" and teaching_event.type == "event"

    teaching_assignment = by_uid["canvas-teaching-assignment-8002"]
    assert teaching_assignment.domain == "mentors"

    # planner_note plannable_type is out of spec scope and must not appear
    assert not any(uid.startswith("canvas-9001") for uid in by_uid)


def test_collect_grades_omits_hidden_totals(client):
    config = Config(canvas_base_url="https://byu.instructure.com")
    grades = canvas.collect_grades(config, client=client)
    by_course = {g["course"]: g for g in grades}

    assert by_course["IS 401"]["grade"] == 94.5
    assert by_course["IS 401"]["letter"] == "A"
    assert by_course["FIN 201"]["grade"] is None  # hidden totals
    assert by_course["FIN 201"]["letter"] is None


def test_is_major_matches_type_points_or_title():
    assert canvas.is_major("exam", None, "Quiz 1", threshold=100)
    assert canvas.is_major("assignment", 150, "Homework", threshold=100)
    assert canvas.is_major("assignment", 10, "Final Project", threshold=100)
    assert not canvas.is_major("assignment", 10, "Homework 3", threshold=100)


def test_missing_canvas_token_raises_clear_error(monkeypatch):
    monkeypatch.setattr("lifeos.collectors.canvas.get_secret", lambda key: None)
    config = Config(canvas_base_url="https://byu.instructure.com")
    with pytest.raises(canvas.CanvasAuthError):
        canvas.collect(config)
