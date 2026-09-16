"""Writes 00 Home/sync-status.md (spec §7): empty when healthy, one line per source failing > 2h."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from lifeos.engine.state import State, hours_failing

UNHEALTHY_THRESHOLD_HOURS = 2


def write_sync_status(vault_path: Path, state: State, now: datetime) -> Path:
    lines = []
    for source in sorted(state.sources):
        hrs = hours_failing(state, source, now)
        if hrs is not None and hrs > UNHEALTHY_THRESHOLD_HOURS:
            err = state.sources[source].last_error_message or "unknown error"
            lines.append(f"- **{source}** failing for {hrs:.1f}h: {err}")

    path = vault_path / "00 Home" / "sync-status.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + ("\n" if lines else ""))
    return path
