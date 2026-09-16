"""lifeos doctor: secret leak scan must catch a token pattern that leaked into a file."""
from __future__ import annotations

from lifeos.doctor import scan_for_leaked_secrets


def test_scan_catches_a_leaked_shopify_token(tmp_path):
    bad = tmp_path / "notes.md"
    bad.write_text("token: shpat_abcdef0123456789abcdef0123456789\n")
    hits = scan_for_leaked_secrets(tmp_path)
    assert len(hits) == 1
    assert "notes.md" in hits[0]


def test_scan_is_clean_for_ordinary_content(tmp_path):
    ok = tmp_path / "notes.md"
    ok.write_text("---\ntitle: Fixture item\n---\nSome ordinary content.\n")
    assert scan_for_leaked_secrets(tmp_path) == []


def test_scan_catches_a_leaked_token_in_a_dotfile(tmp_path):
    """.env has no suffix under pathlib — this is the gap a 2026-09-16 incident exposed."""
    bad = tmp_path / ".env"
    bad.write_text("canvas_token=7407~VAEwZx4QC2CMJzyQDX9v9nM9LXTWJ8ZKRBCTE74G2KZuf3n2KcHRAfT764QVPFEw\n")
    hits = scan_for_leaked_secrets(tmp_path)
    assert len(hits) == 1
    assert ".env" in hits[0]
