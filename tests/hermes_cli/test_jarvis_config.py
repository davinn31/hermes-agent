"""Tests for jarvis config integration — backward-compatible, default section present, no duplication."""
from __future__ import annotations

import pytest
from hermes_cli.config import load_config
from hermes_cli.config_defaults import DEFAULT_CONFIG, _jarvis_defaults


def test_default_config_has_jarvis_section() -> None:
    assert "jarvis" in DEFAULT_CONFIG
    assert isinstance(DEFAULT_CONFIG["jarvis"], dict)
    assert DEFAULT_CONFIG["jarvis"] == _jarvis_defaults()


def test_loaded_config_present_even_without_user_jarvis_section(tmp_path, monkeypatch) -> None:
    """If config.yaml has no jarvis section, the merged config still has one from defaults."""
    import os
    from pathlib import Path

    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))

    # No config.yaml at all is a valid first-run state.
    cfg = load_config()
    jarvis_section = cfg.get("jarvis")
    assert isinstance(jarvis_section, dict)
    assert jarvis_section == _jarvis_defaults()


def test_user_jarvis_section_merged_preserves_other_keys(tmp_path, monkeypatch) -> None:
    """A user config.yaml that sets jarvis.enabled does not drop other jarvis keys."""
    import os
    import yaml
    from pathlib import Path

    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))

    config_path = home / "config.yaml"
    user_config = {"jarvis": {"enabled": True, "preferences": {"communication": {"concise": False}}}}
    config_path.write_text(yaml.safe_dump(user_config), encoding="utf-8")

    cfg = load_config()
    jarvis_section = cfg.get("jarvis")
    assert isinstance(jarvis_section, dict)
    # The user set enabled, but safety defaults still fill the rest.
    assert jarvis_section["enabled"] is True
    assert "instructions" in jarvis_section
    assert "preferences" in jarvis_section
    assert "security" in jarvis_section


def test_jarvis_config_accessors_are_read_only(tmp_path, monkeypatch) -> None:
    """get_jarvis_section returns a plain dict; callers should not mutate it as if it were the static layer."""
    import os
    import yaml
    from pathlib import Path

    from hermes_cli.jarvis_config import get_jarvis_section

    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))

    result = get_jarvis_section()
    assert isinstance(result, dict)
    assert result.get("enabled") is False


def test_jarvis_config_does_not_duplicate_static_definitions(tmp_path, monkeypatch) -> None:
    """Config section must not contain the raw instruction/preference/security text by default."""
    import os
    from pathlib import Path

    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))

    cfg = load_config()
    jarvis = cfg.get("jarvis", {})
    assert isinstance(jarvis, dict)

    assert jarvis.get("instructions") == {}
    assert jarvis.get("preferences") == {}
    assert jarvis.get("security") == {}
