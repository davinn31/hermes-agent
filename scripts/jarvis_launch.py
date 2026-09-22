#!/usr/bin/env python3
"""Jarvis isolated-runtime launcher.

Sets HERMES_HOME to %LOCALAPPDATA%/hermes-jarvis and launches Hermes.
All Jarvis runtime data (config, state, credentials, plugins, memory)
is isolated from the normal Hermes installation at %LOCALAPPDATA%/hermes.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _jarvis_home() -> Path:
    """Resolve the Jarvis Hermes home: %LOCALAPPDATA%/hermes-jarvis."""
    local_appdata = os.environ.get("LOCALAPPDATA", "").strip()
    if local_appdata:
        return Path(local_appdata) / "hermes-jarvis"
    # Fallback: %USERPROFILE%/AppData/Local/hermes-jarvis
    user_profile = os.environ.get("USERPROFILE", "").strip()
    if user_profile:
        return Path(user_profile) / "AppData" / "Local" / "hermes-jarvis"
    # Last resort: relative to this script's parent (repo root)/.hermes-jarvis
    return Path(__file__).resolve().parent.parent / ".hermes-jarvis"


def _project_root() -> Path:
    """Repository root: scripts/.."""
    return Path(__file__).resolve().parent.parent


def build_jarvis_env() -> dict[str, str]:
    """Return a copy of the current environment with HERMES_HOME set for Jarvis."""
    env = os.environ.copy()
    env["HERMES_HOME"] = str(_jarvis_home())
    return env


def main() -> int:
    """Launch Hermes-Jarvis with an isolated runtime home.

    Returns the Hermes process exit code.
    """
    project_root = _project_root()
    jarvis_env = build_jarvis_env()

    # Ensure the project root is on the path so `python -m hermes_cli.main` resolves.
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    result = subprocess.run(
        [sys.executable, "-m", "hermes_cli.main"],
        env=jarvis_env,
        cwd=str(project_root),
        close_fds=False,  # Windows: allow stdin/stdout/stderr inheritance for interactive use
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
