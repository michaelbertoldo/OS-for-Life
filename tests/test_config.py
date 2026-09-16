"""Config loader defaults, and that the example config.toml round-trips."""
from __future__ import annotations

from lifeos.config import Config, load_config, write_example_config


def test_defaults_when_no_config_file(tmp_path):
    config = load_config(tmp_path / "does-not-exist.toml")
    assert config.vault == "~/LifeOS"
    assert config.weights.school == 40


def test_example_config_round_trips(tmp_path):
    path = write_example_config(tmp_path / "config.toml")
    config = load_config(path)
    assert config.timezone == "America/Denver"
    assert config.weights.mentors == 30
