"""Tests for jarvis.identity — importable, side-effect free, contains the established identity."""
from __future__ import annotations

import pytest
from jarvis.identity import IDENTITY, PURPOSE_STATEMENT


def test_identity_module_importable() -> None:
    """jarvis.identity must import cleanly with no side effects."""
    import jarvis.identity as mod

    # A static definition module should expose the expected names.
    assert hasattr(mod, "IDENTITY")
    assert hasattr(mod, "PURPOSE_STATEMENT")


def test_identity_contains_established_statement() -> None:
    """IDENTITY['purpose'] must carry the identity definition established for Jarvis."""
    purpose = IDENTITY["purpose"]
    assert isinstance(purpose, str)

    # The two sentences that define Jarvis's identity.
    assert "Jarvis adalah personal agent yang membantu user berpikir, bekerja, " \
           "membuat software, mencari informasi, dan mengelola pekerjaan digital." in purpose
    assert "Jarvis bertindak sebagai assistant pribadi, bukan sekadar chatbot atau coding assistant." in purpose


def test_purpose_statement_matches_identity_purpose() -> None:
    """PURPOSE_STATEMENT should be the single source of truth for IDENTITY['purpose']."""
    assert PURPOSE_STATEMENT == IDENTITY["purpose"]


def test_identity_is_static_data_not_agent_logic() -> None:
    """Verify the module is definition-only: no function side effects, no runtime work."""
    # Re-importing must not mutate anything or perform I/O; the values are module constants.
    assert isinstance(IDENTITY, dict)
    assert set(IDENTITY.keys()) == {"purpose"}
