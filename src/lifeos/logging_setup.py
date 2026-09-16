"""Logging to ~/Library/Logs/lifeos/sync.log. Structural only: source names and counts,
never secrets or message/email/Slack content.
"""
from __future__ import annotations

import logging
from pathlib import Path

LOG_DIR = Path.home() / "Library" / "Logs" / "lifeos"
LOG_PATH = LOG_DIR / "sync.log"


def get_logger() -> logging.Logger:
    logger = logging.getLogger("lifeos")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(LOG_PATH)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger
