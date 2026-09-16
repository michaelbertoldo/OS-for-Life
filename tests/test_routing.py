"""Routing precedence: source rules first, then config maps, then 'other' (spec §6)."""
from __future__ import annotations

from lifeos.config import Config
from lifeos.engine.routing import route
from lifeos.models import Item


def make_config(**routing_overrides) -> Config:
    return Config.model_validate({"routing": routing_overrides})


def test_already_routed_item_is_left_alone():
    item = Item(domain="mentors", type="event", source="canvas", title="t", uid="u", routed=True)
    config = make_config(sender_domains={"byu.edu": "school"})
    item.sender = "someone@byu.edu"  # would map to school if routing ran
    assert route(item, config) == "mentors"


def test_exact_sender_beats_sender_domain():
    item = Item(domain="other", type="email", source="gmail", title="t", uid="u", sender="prof@byu.edu")
    config = make_config(senders={"prof@byu.edu": "school"}, sender_domains={"byu.edu": "other"})
    assert route(item, config) == "school"


def test_sender_domain_fallback():
    item = Item(domain="other", type="email", source="gmail", title="t", uid="u", sender="someone@byu.edu")
    config = make_config(sender_domains={"byu.edu": "school"})
    assert route(item, config) == "school"


def test_unmatched_falls_back_to_other():
    item = Item(domain="other", type="email", source="gmail", title="t", uid="u", sender="random@example.com")
    config = make_config()
    assert route(item, config) == "other"
