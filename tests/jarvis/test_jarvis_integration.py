"""Integration tests for Jarvis Personal Layer — composition, config→prompt pipeline,
security integration, and cross-component regression."""

from __future__ import annotations

import pytest
from typing import Any
from unittest.mock import MagicMock, patch

# ── Personal Layer composition ────────────────────────────────────────────────

def test_jarvis_personal_layer_composition() -> None:
    """JarvisPersonalLayer should compose identity, instructions, preferences, and security
    without duplicating data — each field is a direct reference to the definition module's constant."""
    from jarvis.personal import JarvisPersonalLayer, PERSONAL_LAYER
    from jarvis.identity import IDENTITY
    from jarvis.instructions import INSTRUCTIONS
    from jarvis.preferences import USER_PREFERENCES
    from jarvis.security import SECURITY_POLICY

    layer = PERSONAL_LAYER
    assert isinstance(layer, JarvisPersonalLayer)
    assert layer.identity is IDENTITY
    assert layer.instructions is INSTRUCTIONS
    assert layer.preferences is USER_PREFERENCES
    assert layer.security_policy is SECURITY_POLICY


def test_jarvis_personal_layer_contains_all_components() -> None:
    """JarvisPersonalLayer must contain all four established components."""
    from jarvis.personal import PERSONAL_LAYER
    from jarvis.identity import PURPOSE_STATEMENT
    from jarvis.instructions import PERSONAL_INSTRUCTIONS
    from jarvis.preferences import USER_PREFERENCES
    from jarvis.security import SECURITY_POLICY, FILESYSTEM_POLICY, TERMINAL_POLICY

    assert "identity" in PERSONAL_LAYER.__dataclass_fields__
    assert PERSONAL_LAYER.identity is not None
    assert "purpose" in PERSONAL_LAYER.identity
    assert PERSONAL_LAYER.identity["purpose"] == PURPOSE_STATEMENT

    assert "instructions" in PERSONAL_LAYER.__dataclass_fields__
    assert PERSONAL_LAYER.instructions is PERSONAL_INSTRUCTIONS
    assert len(PERSONAL_LAYER.instructions) == 8

    assert "preferences" in PERSONAL_LAYER.__dataclass_fields__
    assert PERSONAL_LAYER.preferences is USER_PREFERENCES
    assert "communication" in PERSONAL_LAYER.preferences
    assert "coding" in PERSONAL_LAYER.preferences
    assert "tools" in PERSONAL_LAYER.preferences
    assert "workflow" in PERSONAL_LAYER.preferences

    assert "security_policy" in PERSONAL_LAYER.__dataclass_fields__
    assert PERSONAL_LAYER.security_policy is SECURITY_POLICY
    assert "filesystem" in PERSONAL_LAYER.security_policy
    assert "terminal" in PERSONAL_LAYER.security_policy
    assert PERSONAL_LAYER.security_policy["filesystem"] is FILESYSTEM_POLICY
    assert PERSONAL_LAYER.security_policy["terminal"] is TERMINAL_POLICY


def test_jarvis_personal_layer_no_duplication() -> None:
    """Verify that the personal layer does not contain duplicated data."""
    from jarvis.personal import PERSONAL_LAYER
    from jarvis.identity import IDENTITY
    from jarvis.instructions import INSTRUCTIONS
    from jarvis.preferences import USER_PREFERENCES
    from jarvis.security import SECURITY_POLICY

    assert len(PERSONAL_LAYER.identity) == 1
    assert PERSONAL_LAYER.identity["purpose"] == IDENTITY["purpose"]
    assert PERSONAL_LAYER.identity is IDENTITY

    assert len(PERSONAL_LAYER.instructions) == 8
    assert PERSONAL_LAYER.instructions is INSTRUCTIONS

    assert len(PERSONAL_LAYER.preferences) == 4
    assert PERSONAL_LAYER.preferences is USER_PREFERENCES

    assert len(PERSONAL_LAYER.security_policy) == 2
    assert PERSONAL_LAYER.security_policy is SECURITY_POLICY


# ── Config → Prompt pipeline ──────────────────────────────────────────────────

def test_config_has_jarvis_defaults() -> None:
    """DEFAULT_CONFIG should include a jarvis section with safe defaults."""
    from hermes_cli.config_defaults import DEFAULT_CONFIG, _jarvis_defaults

    assert "jarvis" in DEFAULT_CONFIG
    assert isinstance(DEFAULT_CONFIG["jarvis"], dict)
    assert DEFAULT_CONFIG["jarvis"] == _jarvis_defaults()


def test_loaded_config_preserves_jarvis_section_when_absent(tmp_path, monkeypatch) -> None:
    """Even without a user jarvis config section, the merged config should
    have a jarvis section from defaults (backward compatible)."""
    import os
    from pathlib import Path
    from hermes_cli.config import load_config

    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))

    cfg = load_config()
    jarvis_section = cfg.get("jarvis")
    assert isinstance(jarvis_section, dict)


def test_user_jarvis_section_merged_preserves_other_keys(tmp_path, monkeypatch) -> None:
    """A user config.yaml that sets jarvis.enabled does not drop other jarvis keys."""
    import os
    import yaml
    from pathlib import Path
    from hermes_cli.config import load_config

    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))

    config_path = home / "config.yaml"
    user_config = {"jarvis": {"enabled": True, "preferences": {"communication": {"concise": False}}}}
    config_path.write_text(yaml.safe_dump(user_config), encoding="utf-8")

    cfg = load_config()
    jarvis_section = cfg.get("jarvis")
    assert isinstance(jarvis_section, dict)
    assert jarvis_section["enabled"] is True
    assert "instructions" in jarvis_section
    assert "preferences" in jarvis_section
    assert "security" in jarvis_section


# ── Security integration ──────────────────────────────────────────────────────

def test_filesystem_policy_values() -> None:
    """Verify filesystem policy from jarvis.security has correct values."""
    from jarvis.security import FILESYSTEM_POLICY, ALLOW, DENY

    assert FILESYSTEM_POLICY["READ"] == ALLOW
    assert FILESYSTEM_POLICY["CREATE"] == ALLOW
    assert FILESYSTEM_POLICY["EDIT"] == ALLOW
    assert FILESYSTEM_POLICY["MOVE"] == ALLOW
    assert FILESYSTEM_POLICY["RENAME"] == ALLOW
    assert FILESYSTEM_POLICY["DELETE"] == DENY


def test_terminal_policy_values() -> None:
    """Verify terminal policy from jarvis.security has correct values."""
    from jarvis.security import TERMINAL_POLICY, ALLOW, ASK, DENY

    assert TERMINAL_POLICY["development"] == ALLOW
    assert TERMINAL_POLICY["installation"] == ASK
    assert TERMINAL_POLICY["destructive"] == DENY
    assert TERMINAL_POLICY["secret_exposure"] == DENY


def test_filesystem_guardrail_when_enabled_blocks_delete() -> None:
    """When Jarvis is enabled, ToolCallGuardrailController should block DELETE."""
    from agent.tool_guardrails import ToolCallGuardrailController

    controller = ToolCallGuardrailController()

    with patch.object(controller, "_jarvis_enabled", return_value=True):
        result = controller._check_jarvis_filesystem(
            "skill_manager", {"action": "remove_file", "path": "/tmp/test.txt"}, MagicMock()
        )
        assert result is not None
        assert result.action == "block"


def test_filesystem_guardrail_when_enabled_allows_other_actions() -> None:
    """When Jarvis is enabled, non-DELETE filesystem actions should be allowed."""
    from agent.tool_guardrails import ToolCallGuardrailController

    controller = ToolCallGuardrailController()

    with patch.object(controller, "_jarvis_enabled", return_value=True):
        # READ
        result = controller._check_jarvis_filesystem("read_file", {"path": "/tmp/test.txt"}, MagicMock())
        assert result is None

        # CREATE
        result = controller._check_jarvis_filesystem("write_file", {"path": "/tmp/new.txt", "content": "data"}, MagicMock())
        assert result is None

        # EDIT
        result = controller._check_jarvis_filesystem("patch", {"path": "/tmp/existing.txt", "patch": "change"}, MagicMock())
        assert result is None


def test_filesystem_guardrail_when_disabled_allows_all() -> None:
    """When Jarvis is disabled, all filesystem operations should be allowed."""
    from agent.tool_guardrails import ToolCallGuardrailController

    controller = ToolCallGuardrailController()

    with patch.object(controller, "_jarvis_enabled", return_value=False):
        result = controller._check_jarvis_filesystem(
            "skill_manager", {"action": "remove_file", "path": "/tmp/test.txt"}, MagicMock()
        )
        assert result is None


def test_terminal_guard_when_enabled_blocks_destructive() -> None:
    """When Jarvis is enabled, destructive terminal commands should be blocked."""
    from tools.terminal_tool_guards import jarvis_terminal_block

    with patch("hermes_cli.jarvis_config.get_jarvis_section") as mock_config:
        mock_config.return_value = {"enabled": True}

        result = jarvis_terminal_block("rm -rf /tmp/test")
        assert result is not None
        assert '"exit_code": 1' in result
        assert "BLOCKED" in result

        result = jarvis_terminal_block("ls -la")
        assert result is None


def test_terminal_guard_when_disabled_allows_all() -> None:
    """When Jarvis is disabled, terminal guard should not block any commands."""
    from tools.terminal_tool_guards import jarvis_terminal_block

    with patch("hermes_cli.jarvis_config.get_jarvis_section") as mock_config:
        mock_config.return_value = {"enabled": False}

        result = jarvis_terminal_block("rm -rf /tmp/test")
        assert result is None


def test_terminal_guard_false_positives() -> None:
    """Verify that false positives are avoided."""
    from tools.terminal_tool_guards import jarvis_terminal_block

    with patch("hermes_cli.jarvis_config.get_jarvis_section") as mock_config:
        mock_config.return_value = {"enabled": True}

        # Quoted commands should NOT be blocked
        result = jarvis_terminal_block('echo "rm -rf /"')
        assert result is None

        # git reset --soft should NOT be blocked
        result = jarvis_terminal_block("git reset --soft HEAD~1")
        assert result is None

        # git reset --mixed should NOT be blocked
        result = jarvis_terminal_block("git reset --mixed HEAD~1")
        assert result is None

        # git reset --hard SHOULD be blocked
        result = jarvis_terminal_block("git reset --hard HEAD~1")
        assert result is not None


# ── Cross-component regression ────────────────────────────────────────────────

def test_jarvis_layers_are_consistent() -> None:
    """Verify that all Jarvis layers are consistent and use the same policy source."""
    from jarvis.personal import PERSONAL_LAYER
    from jarvis.security import SECURITY_POLICY

    assert PERSONAL_LAYER.security_policy is SECURITY_POLICY

    fs_policy = PERSONAL_LAYER.security_policy["filesystem"]
    assert fs_policy["READ"] == "ALLOW"
    assert fs_policy["CREATE"] == "ALLOW"
    assert fs_policy["EDIT"] == "ALLOW"
    assert fs_policy["MOVE"] == "ALLOW"
    assert fs_policy["RENAME"] == "ALLOW"
    assert fs_policy["DELETE"] == "DENY"

    term_policy = PERSONAL_LAYER.security_policy["terminal"]
    assert term_policy["development"] == "ALLOW"
    assert term_policy["installation"] == "ASK"
    assert term_policy["destructive"] == "DENY"
    assert term_policy["secret_exposure"] == "DENY"


def test_config_to_security_integration() -> None:
    """End-to-end: config → security enforcement.
    When Jarvis is enabled, security guards should activate."""
    from agent.tool_guardrails import ToolCallGuardrailController
    from tools.terminal_tool_guards import jarvis_terminal_block

    # Filesystem guard
    controller = ToolCallGuardrailController()
    with patch.object(controller, "_jarvis_enabled", return_value=True):
        result = controller._check_jarvis_filesystem(
            "skill_manager", {"action": "remove_file", "path": "/tmp/test.txt"}, MagicMock()
        )
        assert result is not None
        assert result.action == "block"

    # Terminal guard
    with patch("hermes_cli.jarvis_config.get_jarvis_section") as mock_config:
        mock_config.return_value = {"enabled": True}
        result = jarvis_terminal_block("rm -rf /tmp/test")
        assert result is not None
        assert "BLOCKED" in result


def test_disabled_jarvis_preserves_hermescore_behavior() -> None:
    """When Jarvis is disabled, the system should behave as if Jarvis doesn't exist."""
    from agent.tool_guardrails import ToolCallGuardrailController
    from tools.terminal_tool_guards import jarvis_terminal_block

    controller = ToolCallGuardrailController()
    with patch.object(controller, "_jarvis_enabled", return_value=False):
        result = controller._check_jarvis_filesystem(
            "skill_manager", {"action": "remove_file", "path": "/tmp/test.txt"}, MagicMock()
        )
        assert result is None

    with patch("hermes_cli.jarvis_config.get_jarvis_section") as mock_config:
        mock_config.return_value = {}
        result = jarvis_terminal_block("rm -rf /")
        assert result is None


# ── Hermes regression ────────────────────────────────────────────────────────

def test_config_accessors_are_read_only(tmp_path, monkeypatch) -> None:
    """get_jarvis_section returns a plain dict; callers should not mutate it."""
    import os
    from pathlib import Path
    from hermes_cli.jarvis_config import get_jarvis_section

    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))

    result = get_jarvis_section()
    assert isinstance(result, dict)
    assert result.get("enabled") is False


def test_config_does_not_duplicate_static_definitions(tmp_path, monkeypatch) -> None:
    """Config section must not contain the raw instruction/preference/security text."""
    import os
    from pathlib import Path
    from hermes_cli.config import load_config

    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))

    cfg = load_config()
    jarvis = cfg.get("jarvis", {})
    assert isinstance(jarvis, dict)
    assert jarvis.get("instructions") == {}
    assert jarvis.get("preferences") == {}
    assert jarvis.get("security") == {}
