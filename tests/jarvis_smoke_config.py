"""Smoke-test Jarvis config integration through the same import path a real Hermes process uses.

Extends the existing jarvis smoke pattern. Only runs when pytest is unavailable; it does not
replace tests/hermes_cli/test_jarvis_config.py.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

real_home = Path.home()
with tempfile.TemporaryDirectory() as tmp_home:
    monkeypatched_home = Path(tmp_home) / ".hermes"
    monkeypatched_home.mkdir(parents=True, exist_ok=True)
    os.environ["HERMES_HOME"] = str(monkeypatched_home)

    from hermes_cli.config import load_config
    from hermes_cli.config_defaults import DEFAULT_CONFIG, _jarvis_defaults
    from hermes_cli.jarvis_config import get_jarvis_section

    assert "jarvis" in DEFAULT_CONFIG
    assert isinstance(DEFAULT_CONFIG["jarvis"], dict)
    assert DEFAULT_CONFIG["jarvis"] == _jarvis_defaults()

    cfg = load_config()
    assert "jarvis" in cfg
    jarvis_section = cfg.get("jarvis")
    assert isinstance(jarvis_section, dict)
    assert jarvis_section == _jarvis_defaults()

    accessor = get_jarvis_section()
    assert isinstance(accessor, dict)
    assert accessor.get("enabled") is False

print("jarvis_config_smoke: OK")
