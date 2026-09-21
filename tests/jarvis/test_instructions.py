"""Tests for jarvis.instructions — importable, static, contains exactly the 8 established instructions."""
from __future__ import annotations

import pytest
from jarvis.instructions import PERSONAL_INSTRUCTIONS, INSTRUCTIONS


# The eight instructions as established for Jarvis.
_EXPECTED_INSTRUCTIONS: tuple[str, ...] = (
    "1. Prefer solusi sederhana dan hindari kompleksitas yang tidak perlu.",
    "2. Jangan melakukan perubahan destruktif tanpa otorisasi yang sesuai.",
    "3. Jelaskan perubahan penting, terutama perubahan yang berdampak pada system/project.",
    "4. Prioritaskan local execution jika sesuai dan memungkinkan.",
    "5. Jangan mengarang informasi; nyatakan ketidakpastian dengan jelas.",
    "6. Saat coding, pahami existing code sebelum mengubahnya.",
    "7. Bersikap jujur dan kritis, bukan sekadar menyetujui user.",
    "8. Respons harus singkat tetapi tetap mencukupi kebutuhan; hindari detail yang tidak relevan.",
)


def test_instructions_module_importable() -> None:
    import jarvis.instructions as mod

    assert hasattr(mod, "PERSONAL_INSTRUCTIONS")
    assert hasattr(mod, "INSTRUCTIONS")


def test_instructions_exactly_eight() -> None:
    assert len(PERSONAL_INSTRUCTIONS) == 8
    assert PERSONAL_INSTRUCTIONS == _EXPECTED_INSTRUCTIONS


def test_instructions_accessors_are_the_same_object() -> None:
    """INSTRUCTIONS should expose the same tuple callers will actually use."""
    assert INSTRUCTIONS is PERSONAL_INSTRUCTIONS


def test_instructions_are_static_data_not_agent_logic() -> None:
    assert isinstance(PERSONAL_INSTRUCTIONS, tuple)
    assert all(isinstance(item, str) for item in PERSONAL_INSTRUCTIONS)


def test_instructions_deterministic_reimport() -> None:
    """Re-importing must not change the instruction set (no side effects)."""
    import importlib
    import jarvis.instructions as mod

    before = mod.PERSONAL_INSTRUCTIONS
    importlib.reload(mod)
    after = mod.PERSONAL_INSTRUCTIONS
    assert before == after
    assert mod.PERSONAL_INSTRUCTIONS == _EXPECTED_INSTRUCTIONS
