"""The fixture collector never touches the network and returns valid Items."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from lifeos.collectors import fixture
from lifeos.config import Config


def test_fixture_returns_items_across_domains():
    config = Config()
    now = datetime(2026, 9, 16, 15, 0, tzinfo=ZoneInfo("America/Denver"))
    items = fixture.collect(config, now=now)

    assert len(items) >= 5
    domains = {i.domain for i in items}
    assert {"school", "spiced", "mentors", "javvas"}.issubset(domains)
    assert all(i.source == "fixture" for i in items)
