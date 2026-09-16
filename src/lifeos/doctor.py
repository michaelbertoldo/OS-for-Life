"""``lifeos doctor``: config, auth status, vault paths, secret scan, last sync per source."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from lifeos.config import Config
from lifeos.engine.state import State
from lifeos.secrets import LEAK_PATTERNS, has_secret

SCAN_SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".obsidian", "tests"}
SCAN_SUFFIXES = {".md", ".toml", ".json", ".py", ".txt", ".yaml", ".yml"}
# Dotfiles like .env have no suffix under pathlib (the leading dot is treated
# as the whole stem), so `path.suffix` alone would never catch them — exactly
# the kind of file secrets tend to leak into. Match these by name too.
SCAN_DOTFILE_PREFIXES = (".env",)
_LEAK_RE = re.compile("|".join(LEAK_PATTERNS))


@dataclass
class DoctorReport:
    config_ok: bool
    vault_exists: bool
    vault_path: Path
    expected_secrets: dict[str, bool] = field(default_factory=dict)
    leak_hits: list[str] = field(default_factory=list)
    last_sync: dict[str, str | None] = field(default_factory=dict)

    @property
    def healthy(self) -> bool:
        return self.config_ok and not self.leak_hits


def expected_secret_keys(config: Config) -> list[str]:
    keys: list[str] = []
    placeholder = "<school>" in config.canvas_base_url
    if not placeholder:
        keys.append("canvas_token")
    for course in config.learning_suite.courses:
        keys.append(f"ls_feed:{course}")
    if config.google.accounts:
        keys.append("google_client")
        keys += [f"google_token:{a}" for a in config.google.accounts]
    if config.icloud.calendars:
        keys.append("icloud_app_password")
    for account in config.outlook.accounts:
        keys.append(f"outlook_token:{account}")
    for workspace in config.slack.workspaces:
        keys.append(f"slack_token:{workspace}")
    for store in config.shopify.stores:
        keys.append(f"shopify:{store}:client_id")
        keys.append(f"shopify:{store}:client_secret")
    return keys


def scan_for_leaked_secrets(*roots: Path) -> list[str]:
    """Return "path:line" for every line matching a known secret pattern."""
    hits: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            is_scannable = path.suffix in SCAN_SUFFIXES or path.name.startswith(SCAN_DOTFILE_PREFIXES)
            if not is_scannable:
                continue
            if any(part in SCAN_SKIP_DIRS for part in path.parts):
                continue
            try:
                text = path.read_text(errors="ignore")
            except OSError:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if _LEAK_RE.search(line):
                    hits.append(f"{path}:{lineno}")
    return hits


def run_doctor(config: Config, repo_path: Path, state: State) -> DoctorReport:
    report = DoctorReport(
        config_ok=True,
        vault_exists=config.vault_path.exists(),
        vault_path=config.vault_path,
    )
    for key in expected_secret_keys(config):
        report.expected_secrets[key] = has_secret(key)

    report.leak_hits = scan_for_leaked_secrets(repo_path, config.vault_path)

    for source, s in state.sources.items():
        report.last_sync[source] = s.last_success

    return report
