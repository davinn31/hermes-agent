"""Smoke-test jarvis.identity through the same import path a real Hermes process uses.

This is a fallback for environments where the repo venv has no pytest (the canonical
`scripts/run_tests.sh` runner refuses to start without it). It does not replace the
pytest suite in tests/jarvis/test_identity.py — it only proves importability and basic
shape when pytest is unavailable.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Mirror the hermetic home isolation the test suite enforces, so this import cannot
# accidentally read the operator's real ~/.hermes state.
real_home = Path.home()
with tempfile.TemporaryDirectory() as tmp_home:
    monkeypatched_home = Path(tmp_home) / ".hermes"
    monkeypatched_home.mkdir(parents=True, exist_ok=True)
    os.environ["HERMES_HOME"] = str(monkeypatched_home)

    from jarvis.identity import IDENTITY, PURPOSE_STATEMENT  # noqa: F811

    assert isinstance(PURPOSE_STATEMENT, str) and PURPOSE_STATEMENT, "PURPOSE_STATEMENT must be a non-empty str"
    assert isinstance(IDENTITY, dict) and set(IDENTITY.keys()) == {"purpose"}, "IDENTITY must be a dict with only 'purpose'"
    assert IDENTITY["purpose"] is PURPOSE_STATEMENT, "IDENTITY['purpose'] must be the same object as PURPOSE_STATEMENT"

    assert "Jarvis adalah personal agent" in PURPOSE_STATEMENT
    assert "assistant pribadi" in PURPOSE_STATEMENT
    assert "bukan sekadar chatbot atau coding assistant" in PURPOSE_STATEMENT

print("jarvis_identity_smoke: OK")
