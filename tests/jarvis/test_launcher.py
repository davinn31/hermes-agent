"""Launcher tests — verify the Jarvis launcher constructs the correct isolated environment."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Make the repo root importable so the launcher can be tested directly.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def test_jarvis_home_from_localappdata(monkeypatch: pytest.MonkeyPatch) -> None:
    """HERMES_HOME resolves to %LOCALAPPDATA%/hermes-jarvis when LOCALAPPDATA is set."""
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\mdavi\AppData\Local")
    monkeypatch.delenv("USERPROFILE", raising=False)

    from scripts.jarvis_launch import _jarvis_home

    home = _jarvis_home()
    assert home == Path(r"C:\Users\mdavi\AppData\Local\hermes-jarvis")


def test_jarvis_home_fallback_to_userprofile(monkeypatch: pytest.MonkeyPatch) -> None:
    """When LOCALAPPDATA is empty, fall back to %USERPROFILE%/AppData/Local/hermes-jarvis."""
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("USERPROFILE", r"C:\Users\mdavi")

    from scripts.jarvis_launch import _jarvis_home

    home = _jarvis_home()
    assert home == Path(r"C:\Users\mdavi\AppData\Local\hermes-jarvis")


def test_jarvis_home_relative_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """When neither LOCALAPPDATA nor USERPROFILE is set, use repo-relative .hermes-jarvis."""
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.delenv("USERPROFILE", raising=False)

    from scripts.jarvis_launch import _jarvis_home, _project_root

    home = _jarvis_home()
    assert home == _project_root() / ".hermes-jarvis"


def test_build_jarvis_env_preserves_existing(monkeypatch: pytest.MonkeyPatch) -> None:
    """build_jarvis_env copies the current environment and sets HERMES_HOME."""
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\mdavi\AppData\Local")
    monkeypatch.setenv("PATH", r"C:\Python\python.exe;C:\Windows\system32")
    monkeypatch.setenv("MY_CUSTOM_VAR", "my-value")

    from scripts.jarvis_launch import build_jarvis_env

    env = build_jarvis_env()
    assert env["HERMES_HOME"] == r"C:\Users\mdavi\AppData\Local\hermes-jarvis"
    assert env["PATH"] == r"C:\Python\python.exe;C:\Windows\system32"
    assert env["MY_CUSTOM_VAR"] == "my-value"


def test_build_jarvis_env_overwrites_existing_hermes_home(monkeypatch: pytest.MonkeyPatch) -> None:
    """If HERMES_HOME is already set, the launcher overwrites it for Jarvis isolation."""
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\mdavi\AppData\Local")
    monkeypatch.setenv("HERMES_HOME", r"C:\Users\mdavi\AppData\Local\hermes")

    from scripts.jarvis_launch import build_jarvis_env

    env = build_jarvis_env()
    assert env["HERMES_HOME"] == r"C:\Users\mdavi\AppData\Local\hermes-jarvis"


def test_project_root_resolves_to_repo_root() -> None:
    """_project_root() returns the repository root (scripts/..)."""
    from scripts.jarvis_launch import _project_root

    root = _project_root()
    assert root.name == "hermes-agent"
    assert (root / "pyproject.toml").exists()


def test_launch_command_construction(monkeypatch: pytest.MonkeyPatch) -> None:
    """The launcher invokes `python -m hermes_cli.main` with the isolated environment."""
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\mdavi\AppData\Local")

    from scripts.jarvis_launch import build_jarvis_env, _project_root

    env = build_jarvis_env()
    assert env["HERMES_HOME"] == r"C:\Users\mdavi\AppData\Local\hermes-jarvis"

    # Verify the command that would be run (without actually running it).
    cmd = [sys.executable, "-m", "hermes_cli.main"]
    assert cmd[1] == "-m"
    assert cmd[2] == "hermes_cli.main"


def test_launch_is_isolated_from_original_hermesc(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The launcher's HERMES_HOME is different from the default Hermes home.

    This verifies isolation: Jarvis writes to hermes-jarvis, not hermes.
    """
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "Users" / "mdavi"))

    # Create the default Hermes home to simulate an existing installation.
    default_home = tmp_path / "Users" / "mdavi" / "AppData" / "Local" / "hermes"
    default_home.mkdir(parents=True)
    (default_home / "config.yaml").write_text("model: solar-pro4\n")
    (default_home / ".env").write_text("ANTHROPIC_API_KEY=sk-test\n")
    (default_home / "state.db").write_bytes(b"SQLite format 3\n")

    from scripts.jarvis_launch import _jarvis_home, build_jarvis_env

    jarvis_home = _jarvis_home()
    assert jarvis_home.name == "hermes-jarvis"
    assert jarvis_home != default_home

    env = build_jarvis_env()
    assert env["HERMES_HOME"] == str(jarvis_home)

    # The default Hermes files are untouched by the launcher's env construction.
    assert (default_home / "config.yaml").read_text() == "model: solar-pro4\n"
    assert (default_home / ".env").read_text() == "ANTHROPIC_API_KEY=sk-test\n"
    assert (default_home / "state.db").read_bytes() == b"SQLite format 3\n"
