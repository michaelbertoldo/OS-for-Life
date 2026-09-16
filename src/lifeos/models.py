"""The Item model: every synced item and every manual task is one of these (spec §4)."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Domain = Literal["school", "mentors", "spiced", "javvas", "other"]
ItemType = Literal[
    "assignment", "exam", "event", "announcement", "message",
    "email", "slack", "order", "inventory", "task",
]
Status = Literal["open", "done", "snoozed"]
Source = Literal[
    "canvas", "learning-suite", "gcal", "icloud", "gmail",
    "outlook", "slack", "shopify", "manual", "fixture",
]


class Item(BaseModel):
    # Core properties
    domain: Domain
    type: ItemType
    due: datetime | None = None
    score: float = 0.0
    status: Status = "open"
    source: Source
    link: str = ""

    # Context properties (hidden unless a view needs them)
    title: str
    uid: str
    course: str | None = None
    platform: Literal["canvas", "learning-suite"] | None = None
    received: datetime | None = None
    account: str | None = None
    goal: str | None = None

    # Not persisted as a vault property; used only for routing/scoring input.
    sender: str | None = Field(default=None, exclude=True)
    is_major: bool = False

    # True when the collector already assigned domain via a source rule
    # (teaching course -> mentors, store -> spiced/javvas). Routing then
    # leaves it alone instead of applying the config maps. Not persisted.
    routed: bool = Field(default=False, exclude=True)
