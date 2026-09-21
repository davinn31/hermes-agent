"""Smoke-test jarvis.preferences when the repo venv has no pytest (extends the existing smoke pattern)."""
from __future__ import annotations

import importlib
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

EXPECTED_PREFERENCES: dict[str, dict[str, object]] = {
    "communication": {"concise": True},
    "coding": {"understand_existing_code_first": True},
    "tools": {"prefer_local_execution": True},
    "workflow": {"prefer_simple_solution": True},
}

real_home = Path.home()
with tempfile.TemporaryDirectory() as tmp_home:
    monkeypatched_home = Path(tmp_home) / ".hermes"
    monkeypatched_home.mkdir(parents=True, exist_ok=True)
    os.environ["HERMES_HOME"] = str(monkeypatched_home)

    import jarvis.preferences as mod

    assert isinstance(mod.PREFERENCES, dict), "PREFERENCES must be a dict"
    assert set(mod.PREFERENCES.keys()) == set(EXPECTED_PREFERENCES.keys()), "must have exactly the 4 established categories"
    assert mod.PREFERENCES == EXPECTED_PREFERENCES, "defaults must match the established definition"
    assert mod.USER_PREFERENCES is mod.PREFERENCES, "USER_PREFERENCES must alias PREFERENCES"

    # All leaf values are booleans as established (user defaults, not runtime flags).
    for category, prefs in mod.PREFERENCES.items():
        assert isinstance(prefs, dict)
        assert all(isinstance(v, bool) for v in prefs.values())

    # Re-import must not mutate anything.
    before = mod.PREFERENCES
    importlib.reload(mod)
    after = mod.PREFERENCES
    assert before == after == EXPECTED_PREFERENCES

    # Must stay distinct from instructions.
    import jarvis.instructions as instructions_mod
    assert hasattr(instructions_mod, "PERSONAL_INSTRUCTIONS")
    assert not hasattr(instructions_mod, "PREFERENCES")

print("jarvis_preferences_smoke: OK")
