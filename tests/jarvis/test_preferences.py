"""Tests for jarvis.preferences — importable, exactly the 4 established categories, static."""
from __future__ import annotations

import importlib
import pytest
from jarvis.preferences import PREFERENCES, USER_PREFERENCES

# Exactly the four established preference categories and their defaults.
_EXPECTED_PREFERENCES: dict[str, dict[str, object]] = {
    "communication": {"concise": True},
    "coding": {"understand_existing_code_first": True},
    "tools": {"prefer_local_execution": True},
    "workflow": {"prefer_simple_solution": True},
}


def test_preferences_module_importable() -> None:
    import jarvis.preferences as mod

    assert hasattr(mod, "PREFERENCES")
    assert hasattr(mod, "USER_PREFERENCES")


def test_preferences_exactly_four_categories() -> None:
    assert set(PREFERENCES.keys()) == set(_EXPECTED_PREFERENCES.keys())
    assert PREFERENCES == _EXPECTED_PREFERENCES


def test_preferences_accessors_are_the_same_object() -> None:
    """USER_PREFERENCES should expose the same dict callers will actually use."""
    assert USER_PREFERENCES is PREFERENCES


def test_preferences_are_static_data_not_agent_logic() -> None:
    assert isinstance(PREFERENCES, dict)
    for category, prefs in PREFERENCES.items():
        assert isinstance(category, str)
        assert isinstance(prefs, dict)
        assert all(isinstance(v, bool) for v in prefs.values())


def test_preferences_deterministic_reimport() -> None:
    """Re-importing must not change the preference set (no side effects)."""
    import jarvis.preferences as mod

    before = mod.PREFERENCES
    importlib.reload(mod)
    after = mod.PREFERENCES
    assert before == after == _EXPECTED_PREFERENCES


def test_preferences_distinct_from_instructions() -> None:
    """Preferences must not bleed into instructions and vice-versa."""
    import jarvis.instructions as instructions_mod
    import jarvis.preferences as prefs_mod

    assert hasattr(instructions_mod, "PERSONAL_INSTRUCTIONS")
    assert hasattr(prefs_mod, "PREFERENCES")
    assert not hasattr(instructions_mod, "PREFERENCES")
    assert not hasattr(prefs_mod, "PERSONAL_INSTRUCTIONS")
