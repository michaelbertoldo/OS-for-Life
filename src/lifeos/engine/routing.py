"""Routing, per spec §6.

Precedence: source rules first (a collector sets ``item.domain`` and
``item.routed = True`` for a teaching course -> mentors or a store ->
spiced/javvas). Anything not already routed falls through the config maps
below, in order: exact sender, sender domain, calendar, Slack workspace.
Anything left is "other".
"""
from __future__ import annotations

from lifeos.config import Config
from lifeos.models import Domain, Item


def route(item: Item, config: Config) -> Domain:
    if item.routed:
        return item.domain

    if item.sender:
        if item.sender in config.routing.senders:
            return config.routing.senders[item.sender]  # type: ignore[return-value]
        domain_part = item.sender.rsplit("@", 1)[-1]
        if domain_part in config.routing.sender_domains:
            return config.routing.sender_domains[domain_part]  # type: ignore[return-value]

    if item.account:
        if item.account in config.google.calendar_domains:
            return config.google.calendar_domains[item.account]  # type: ignore[return-value]
        if item.account in config.slack.workspaces:
            return config.slack.workspaces[item.account]  # type: ignore[return-value]

    return "other"
