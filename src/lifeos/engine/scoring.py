"""Scoring, per spec §6. Do not change the thresholds without updating docs/SPEC.md and the tests."""
from __future__ import annotations

from datetime import datetime

from lifeos.config import WeightsConfig
from lifeos.models import Item


def score(item: Item, now: datetime, weights: WeightsConfig, vip: list[str]) -> float:
    s = float(getattr(weights, item.domain))
    if item.due:
        h = (item.due - now).total_seconds() / 3600
        if h < 0:
            s += 50  # overdue or missing
        elif h <= 24:
            s += 40
        elif h <= 72:
            s += 25
        elif h <= 168:
            s += 10
    if item.sender and item.sender in vip:
        s += 15
    if item.is_major:
        s += 10
    return s
