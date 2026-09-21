"""Tests for jarvis.security — importable policy definition, exact established actions/categories, static."""
from __future__ import annotations

import importlib
import pytest
from jarvis.security import (
    ALLOW,
    ASK,
    DENY,
    FILESYSTEM_POLICY,
    TERMINAL_POLICY,
    SECURITY_POLICY,
    POLICY,
)


def test_security_module_importable() -> None:
    import jarvis.security as mod

    assert hasattr(mod, "ALLOW")
    assert hasattr(mod, "ASK")
    assert hasattr(mod, "DENY")
    assert hasattr(mod, "FILESYSTEM_POLICY")
    assert hasattr(mod, "TERMINAL_POLICY")
    assert hasattr(mod, "SECURITY_POLICY")
    assert hasattr(mod, "POLICY")


def test_security_decisions_defined() -> None:
    assert ALLOW == "ALLOW"
    assert ASK == "ASK"
    assert DENY == "DENY"
    assert {ALLOW, ASK, DENY} == {"ALLOW", "ASK", "DENY"}


def test_filesystem_policy_exactly_six_actions() -> None:
    assert set(FILESYSTEM_POLICY.keys()) == {
        "READ",
        "CREATE",
        "EDIT",
        "MOVE",
        "RENAME",
        "DELETE",
    }
    assert len(FILESYSTEM_POLICY) == 6


def test_filesystem_policy_decisions_match_brief() -> None:
    assert FILESYSTEM_POLICY["READ"] == ALLOW
    assert FILESYSTEM_POLICY["CREATE"] == ALLOW
    assert FILESYSTEM_POLICY["EDIT"] == ALLOW
    assert FILESYSTEM_POLICY["MOVE"] == ALLOW
    assert FILESYSTEM_POLICY["RENAME"] == ALLOW
    assert FILESYSTEM_POLICY["DELETE"] == DENY


def test_terminal_policy_exactly_four_categories() -> None:
    assert set(TERMINAL_POLICY.keys()) == {
        "development",
        "installation",
        "destructive",
        "secret_exposure",
    }
    assert len(TERMINAL_POLICY) == 4


def test_terminal_policy_decisions_match_brief() -> None:
    assert TERMINAL_POLICY["development"] == ALLOW
    assert TERMINAL_POLICY["installation"] == ASK
    assert TERMINAL_POLICY["destructive"] == DENY
    assert TERMINAL_POLICY["secret_exposure"] == DENY


def test_security_policy_container_matches_parts() -> None:
    assert SECURITY_POLICY == {"filesystem": FILESYSTEM_POLICY, "terminal": TERMINAL_POLICY}
    assert POLICY is SECURITY_POLICY


def test_only_allowed_decisions_appear_in_policy() -> None:
    all_decisions = set(FILESYSTEM_POLICY.values()) | set(TERMINAL_POLICY.values())
    assert all_decisions <= {ALLOW, ASK, DENY}


def test_security_policy_is_static_data_not_enforcement() -> None:
    assert isinstance(SECURITY_POLICY, dict)
    for section in SECURITY_POLICY.values():
        assert isinstance(section, dict)
        assert all(isinstance(k, str) and isinstance(v, str) for k, v in section.items())


def test_security_policy_deterministic_after_reload() -> None:
    import jarvis.security as mod

    before = dict(mod.SECURITY_POLICY)
    importlib.reload(mod)
    after = dict(mod.SECURITY_POLICY)
    assert before == after
    assert mod.FILESYSTEM_POLICY == {
        "READ": mod.ALLOW,
        "CREATE": mod.ALLOW,
        "EDIT": mod.ALLOW,
        "MOVE": mod.ALLOW,
        "RENAME": mod.ALLOW,
        "DELETE": mod.DENY,
    }
    assert mod.TERMINAL_POLICY == {
        "development": mod.ALLOW,
        "installation": mod.ASK,
        "destructive": mod.DENY,
        "secret_exposure": mod.DENY,
    }
