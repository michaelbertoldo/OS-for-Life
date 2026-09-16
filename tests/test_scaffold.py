"""Vault scaffolding never overwrites a file that already exists (spec §3)."""
from __future__ import annotations

from lifeos.scaffold import scaffold_vault


def test_scaffold_creates_expected_structure(tmp_path):
    created = scaffold_vault(tmp_path)
    assert created  # something was created
    assert (tmp_path / "00 Home" / "Today.md").exists()
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / "AGENTS.md").is_symlink()
    assert (tmp_path / "90 Sync").is_dir()
    assert (tmp_path / "_templates" / "task.md").exists()


def test_scaffold_never_overwrites_existing_file(tmp_path):
    scaffold_vault(tmp_path)
    today = tmp_path / "00 Home" / "Today.md"
    today.write_text("Michael's own content")

    scaffold_vault(tmp_path)  # run again
    assert today.read_text() == "Michael's own content"
