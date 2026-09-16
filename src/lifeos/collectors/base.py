"""Collector protocol: one module per source, read-only access, returns normalized Items."""
from __future__ import annotations

from typing import Protocol

from lifeos.config import Config
from lifeos.models import Item


class Collector(Protocol):
    name: str

    def collect(self, config: Config) -> list[Item]:
        ...
