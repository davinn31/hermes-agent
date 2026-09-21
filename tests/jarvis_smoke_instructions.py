"""Smoke-test jarvis.instructions when the repo venv has no pytest (same gap as Task 01/02)."""
from __future__ import annotations

import importlib
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

EXPECTED_INSTRUCTIONS: tuple[str, ...] = (
    "1. Prefer solusi sederhana dan hindari kompleksitas yang tidak perlu.",
    "2. Jangan melakukan perubahan destruktif tanpa otorisasi yang sesuai.",
    "3. Jelaskan perubahan penting, terutama perubahan yang berdampak pada system/project.",
    "4. Prioritaskan local execution jika sesuai dan memungkinkan.",
    "5. Jangan mengarang informasi; nyatakan ketidakpastian dengan jelas.",
    "6. Saat coding, pahami existing code sebelum mengubahnya.",
    "7. Bersikap jujur dan kritis, bukan sekadar menyetujui user.",
    "8. Respons harus singkat tetapi tetap mencukupi kebutuhan; hindari detail yang tidak relevan.",
)

real_home = Path.home()
with tempfile.TemporaryDirectory() as tmp_home:
    monkeypatched_home = Path(tmp_home) / ".hermes"
    monkeypatched_home.mkdir(parents=True, exist_ok=True)
    os.environ["HERMES_HOME"] = str(monkeypatched_home)

    import jarvis.instructions as mod

    assert isinstance(mod.PERSONAL_INSTRUCTIONS, tuple)
    assert mod.PERSONAL_INSTRUCTIONS == EXPECTED_INSTRUCTIONS
    assert mod.INSTRUCTIONS is mod.PERSONAL_INSTRUCTIONS
    assert len(mod.PERSONAL_INSTRUCTIONS) == 8

    # Re-import must not mutate anything.
    before = mod.PERSONAL_INSTRUCTIONS
    importlib.reload(mod)
    after = mod.PERSONAL_INSTRUCTIONS
    assert before == after == EXPECTED_INSTRUCTIONS

print("jarvis_instructions_smoke: OK")
