"""Canvas collector (spec §5.1).

Field names for planner items, missing submissions, and enrollment grades were
verified against Canvas's current API docs (developerdocs.instructure.com,
checked 2026-09-16) before writing this: plannable objects use ``name`` and
``due_at``; StudentEnrollment grades use ``current_score``/``current_grade``,
omitted entirely when the professor hides totals. Announcement and
conversation field names follow long-standing, stable Canvas API convention
but weren't independently re-confirmed against the live docs in this session
(a fetch timed out) — the first real ``--dry-run`` (rule 7) is the checkpoint
that catches any drift before anything is written.

Only pulls what needs action. Teacher enrollments (the Mentors International
pilot course) pull only calendar events and due dates — never student names,
submissions, grades, or conversations (FERPA).
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta

import httpx

from lifeos.config import Config
from lifeos.models import Item
from lifeos.secrets import get_secret

name = "canvas"

MAJOR_TITLE_PATTERN = re.compile(r"\b(exam|midterm|final|project)\b", re.IGNORECASE)


class CanvasAuthError(RuntimeError):
    pass


def _client(config: Config) -> httpx.Client:
    token = get_secret("canvas_token")
    if not token:
        raise CanvasAuthError(
            "canvas_token not found in Keychain. Run: uv run lifeos secret set canvas_token"
        )
    return httpx.Client(
        base_url=config.canvas_base_url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )


def _paginated_get(client: httpx.Client, path: str, params: dict | None = None) -> list[dict]:
    results: list[dict] = []
    resp = client.get(path, params=params)
    resp.raise_for_status()
    results.extend(resp.json())
    next_url = _next_link(resp.headers.get("Link"))
    while next_url:
        resp = client.get(next_url)
        resp.raise_for_status()
        results.extend(resp.json())
        next_url = _next_link(resp.headers.get("Link"))
    return results


def _next_link(link_header: str | None) -> str | None:
    if not link_header:
        return None
    for part in link_header.split(","):
        segments = part.split(";")
        if len(segments) < 2:
            continue
        url = segments[0].strip().strip("<>")
        rel = segments[1].strip()
        if rel == 'rel="next"':
            return url
    return None


def is_major(item_type: str, points_possible: float | None, title: str, threshold: int) -> bool:
    if item_type == "exam":
        return True
    if points_possible is not None and points_possible >= threshold:
        return True
    return bool(MAJOR_TITLE_PATTERN.search(title or ""))


def _course_names(client: httpx.Client) -> dict[int, str]:
    courses = _paginated_get(client, "/api/v1/courses", params={"enrollment_state": "active"})
    return {c["id"]: c.get("course_code") or c.get("name") for c in courses}


def collect(config: Config, client: httpx.Client | None = None, now: datetime | None = None) -> list[Item]:
    now = now or datetime.now().astimezone()
    owns_client = client is None
    client = client or _client(config)
    try:
        items: list[Item] = []
        course_names = _course_names(client)

        enrollments = _paginated_get(client, "/api/v1/users/self/enrollments", params={"state[]": "active"})
        student_courses = [e["course_id"] for e in enrollments if e.get("type") == "StudentEnrollment"]
        teacher_courses = [e["course_id"] for e in enrollments if e.get("type") == "TeacherEnrollment"]

        items += _collect_student_items(client, config, now, student_courses, course_names)
        items += _collect_teaching_course_items(client, teacher_courses, course_names, now)

        return items
    finally:
        if owns_client:
            client.close()


def _collect_student_items(
    client: httpx.Client, config: Config, now: datetime, course_ids: list[int], course_names: dict[int, str],
) -> list[Item]:
    items: dict[str, Item] = {}
    threshold = config.canvas.major_points_threshold

    planner_items = _paginated_get(
        client, "/api/v1/planner/items",
        params={
            "start_date": (now - timedelta(days=14)).date().isoformat(),
            "end_date": (now + timedelta(days=30)).date().isoformat(),
        },
    )
    for raw in planner_items:
        plannable_type = raw.get("plannable_type")
        if plannable_type not in ("assignment", "quiz"):
            continue
        plannable = raw.get("plannable") or {}
        course_id = raw.get("course_id")
        item_type = "exam" if plannable_type == "quiz" else "assignment"
        title = plannable.get("name", "")
        submissions = raw.get("submissions") or {}
        done = bool(submissions.get("graded") or submissions.get("excused"))
        uid = f"canvas-assignment-{plannable.get('id')}"
        items[uid] = Item(
            domain="school",
            type=item_type,
            due=_parse_canvas_dt(plannable.get("due_at")),
            status="done" if done else "open",
            source="canvas",
            link=raw.get("html_url", ""),
            title=title,
            uid=uid,
            course=course_names.get(course_id, str(course_id)),
            platform="canvas",
            is_major=is_major(item_type, plannable.get("points_possible"), title, threshold),
            routed=True,
        )

    missing = _paginated_get(client, "/api/v1/users/self/missing_submissions")
    for raw in missing:
        uid = f"canvas-assignment-{raw.get('id')}"
        title = raw.get("name", "")
        item_type = "assignment"
        if uid in items:
            items[uid] = items[uid].model_copy(update={"status": "open"})
            continue
        items[uid] = Item(
            domain="school",
            type=item_type,
            due=_parse_canvas_dt(raw.get("due_at")),
            status="open",
            source="canvas",
            link=raw.get("html_url", ""),
            title=title,
            uid=uid,
            course=course_names.get(raw.get("course_id"), str(raw.get("course_id"))),
            platform="canvas",
            is_major=is_major(item_type, raw.get("points_possible"), title, threshold),
            routed=True,
        )

    announcements = _paginated_get(
        client, "/api/v1/announcements",
        params={
            "context_codes[]": [f"course_{c}" for c in course_ids],
            "start_date": (now - timedelta(days=14)).date().isoformat(),
        },
    )
    for raw in announcements:
        if raw.get("read_state") != "unread":
            continue
        uid = f"canvas-announcement-{raw.get('id')}"
        course_id = None
        ctx = raw.get("context_code", "")
        if ctx.startswith("course_"):
            course_id = int(ctx.removeprefix("course_"))
        items[uid] = Item(
            domain="school",
            type="announcement",
            due=None,
            status="open",
            source="canvas",
            link=raw.get("html_url", ""),
            title=raw.get("title", ""),
            uid=uid,
            course=course_names.get(course_id, str(course_id) if course_id else None),
            platform="canvas",
            received=_parse_canvas_dt(raw.get("posted_at")),
            routed=True,
        )

    conversations = _paginated_get(client, "/api/v1/conversations", params={"scope": "unread"})
    for raw in conversations:
        uid = f"canvas-message-{raw.get('id')}"
        items[uid] = Item(
            domain="school",
            type="message",
            due=None,
            status="open",
            source="canvas",
            link=f"{client.base_url}conversations#filter=type=inbox",
            title=raw.get("subject") or "(no subject)",
            uid=uid,
            platform="canvas",
            received=_parse_canvas_dt(raw.get("last_message_at")),
            routed=True,
        )

    return list(items.values())


def _collect_teaching_course_items(
    client: httpx.Client, course_ids: list[int], course_names: dict[int, str], now: datetime,
) -> list[Item]:
    """Mentors International pilot course: events and due dates only. No student data (FERPA)."""
    items: list[Item] = []
    for course_id in course_ids:
        events = _paginated_get(
            client, "/api/v1/calendar_events",
            params={"context_codes[]": [f"course_{course_id}"], "type": "event"},
        )
        for raw in events:
            uid = f"canvas-event-{raw.get('id')}"
            items.append(Item(
                domain="mentors",
                type="event",
                due=_parse_canvas_dt(raw.get("start_at")),
                status="open",
                source="canvas",
                link=raw.get("html_url", ""),
                title=raw.get("title", ""),
                uid=uid,
                platform="canvas",
                routed=True,
            ))

        assignments = _paginated_get(client, f"/api/v1/courses/{course_id}/assignments")
        for raw in assignments:
            uid = f"canvas-teaching-assignment-{raw.get('id')}"
            title = raw.get("name", "")
            items.append(Item(
                domain="mentors",
                type="assignment",
                due=_parse_canvas_dt(raw.get("due_at")),
                status="open",
                source="canvas",
                link=raw.get("html_url", ""),
                title=title,
                uid=uid,
                platform="canvas",
                routed=True,
            ))
    return items


def collect_grades(config: Config, client: httpx.Client | None = None) -> list[dict]:
    """Grades per active StudentEnrollment. §5.1: create the course note if it's
    missing; leave grade empty and letter "hidden" when the professor hides totals
    (the API simply omits current_score/current_grade in that case)."""
    owns_client = client is None
    client = client or _client(config)
    try:
        course_names = _course_names(client)
        enrollments = _paginated_get(client, "/api/v1/users/self/enrollments", params={"state[]": "active"})
        results = []
        for e in enrollments:
            if e.get("type") != "StudentEnrollment":
                continue
            grades = e.get("grades") or {}
            results.append({
                "course": course_names.get(e.get("course_id"), str(e.get("course_id"))),
                "platform": "canvas",
                "grade": grades.get("current_score"),
                "letter": grades.get("current_grade"),
            })
        return results
    finally:
        if owns_client:
            client.close()


def _parse_canvas_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
