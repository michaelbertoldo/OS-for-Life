"""Fixture source (spec P0-11): synthetic items, no network, used to verify the pipeline
end to end (routing, scoring, vault write, Obsidian Bases property types) before any
real collector exists.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from lifeos.config import Config
from lifeos.models import Item

name = "fixture"


def collect(config: Config, now: datetime | None = None) -> list[Item]:
    now = now or datetime.now().astimezone()
    return [
        Item(
            domain="school",
            type="assignment",
            due=now + timedelta(hours=20),
            source="fixture",
            title="Fixture: Problem Set 4",
            uid="fixture-school-assignment-1",
            course="IS 401",
            routed=True,
        ),
        Item(
            domain="spiced",
            type="order",
            due=now - timedelta(hours=2),
            source="fixture",
            title="Fixture: Unfulfilled order #1042",
            uid="fixture-spiced-order-1",
            account="spiced",
            routed=True,
        ),
        Item(
            domain="mentors",
            type="event",
            due=now + timedelta(hours=3),
            source="fixture",
            title="Fixture: Mentors International weekly sync",
            uid="fixture-mentors-event-1",
            routed=True,
        ),
        Item(
            domain="javvas",
            type="inventory",
            due=None,
            source="fixture",
            title="Fixture: Low stock - Javvas hoodie (M)",
            uid="fixture-javvas-inventory-1",
            account="javvas",
            routed=True,
        ),
        Item(
            domain="other",
            type="email",
            due=None,
            source="fixture",
            title="Fixture: Newsletter digest",
            uid="fixture-other-email-1",
            account="personal",
            received=now - timedelta(hours=5),
            sender="digest@example.com",
            routed=True,
        ),
    ]
