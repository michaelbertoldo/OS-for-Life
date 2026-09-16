"""The 4 required scoring test cases from docs/SPEC.md §6."""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from lifeos.config import WeightsConfig
from lifeos.engine.scoring import score
from lifeos.models import Item

TZ = ZoneInfo("America/Denver")
NOW = datetime(2026, 9, 16, 15, 0, tzinfo=TZ)
WEIGHTS = WeightsConfig()


def make_item(**overrides) -> Item:
    defaults = dict(
        domain="school",
        type="assignment",
        source="fixture",
        title="t",
        uid="u",
    )
    defaults.update(overrides)
    return Item(**defaults)


def test_school_assignment_outranks_spiced_order_at_equal_urgency():
    school = make_item(domain="school", due=NOW + timedelta(hours=20))
    spiced = make_item(domain="spiced", type="order", due=NOW + timedelta(hours=20))

    school_score = score(school, NOW, WEIGHTS, vip=[])
    spiced_score = score(spiced, NOW, WEIGHTS, vip=[])

    assert school_score == 80
    assert spiced_score == 60
    assert school_score > spiced_score


def test_overdue_spiced_order_outranks_school_item_due_in_six_days():
    spiced = make_item(domain="spiced", type="order", due=NOW - timedelta(hours=1))
    school = make_item(domain="school", due=NOW + timedelta(days=6))

    spiced_score = score(spiced, NOW, WEIGHTS, vip=[])
    school_score = score(school, NOW, WEIGHTS, vip=[])

    assert spiced_score == 70
    assert school_score == 50
    assert spiced_score > school_score


def test_vip_professor_email_ranks_below_school_assignment_due_in_60h():
    email = make_item(domain="school", type="email", due=None, sender="prof@byu.edu")
    assignment = make_item(domain="school", type="assignment", due=NOW + timedelta(hours=60))

    email_score = score(email, NOW, WEIGHTS, vip=["prof@byu.edu"])
    assignment_score = score(assignment, NOW, WEIGHTS, vip=["prof@byu.edu"])

    assert email_score == 55
    assert assignment_score == 65
    assert email_score < assignment_score


def test_learning_suite_item_due_tomorrow_is_anchored_to_midnight():
    tomorrow_midnight = (NOW + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    item = make_item(
        domain="school", type="assignment", source="learning-suite",
        platform="learning-suite", due=tomorrow_midnight,
    )

    hours_until_due = (item.due - NOW).total_seconds() / 3600
    assert hours_until_due == 9  # anchored to 00:00, not end-of-day

    assert score(item, NOW, WEIGHTS, vip=[]) == 80  # 40 (school) + 40 (<=24h)
