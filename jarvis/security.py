"""Jarvis security policy definition — static source of truth for filesystem and terminal decisions.

Definition only. No enforcement, no guard wiring, no secret storage, no command
detection. Enforcement is deferred to a later task.
"""

from __future__ import annotations

# Decision vocabulary for Jarvis security policy.
ALLOW = "ALLOW"
ASK = "ASK"
DENY = "DENY"

_VALID_DECISIONS = frozenset({ALLOW, ASK, DENY})

# Filesystem actions → decisions, as established for the Jarvis Personal Layer.
FILESYSTEM_POLICY: dict[str, str] = {
    "READ": ALLOW,
    "CREATE": ALLOW,
    "EDIT": ALLOW,
    "MOVE": ALLOW,
    "RENAME": ALLOW,
    "DELETE": DENY,
}

# Terminal operation categories → decisions, as established for the Jarvis Personal Layer.
TERMINAL_POLICY: dict[str, str] = {
    "development": ALLOW,
    "installation": ASK,
    "destructive": DENY,
    "secret_exposure": DENY,
}

# Top-level container so callers can fetch the entire policy in one import without
# guessing the field names. Mirrors the accessor shape used by jarvis.identity and
# jarvis.preferences.
SECURITY_POLICY: dict[str, dict[str, str]] = {
    "filesystem": FILESYSTEM_POLICY,
    "terminal": TERMINAL_POLICY,
}

# Convenience accessor for enforcement/prompt integration without guessing the
# top-level field name.
POLICY: dict[str, dict[str, str]] = SECURITY_POLICY


def _validate_policy(policy: dict[str, str]) -> None:
    """Lightweight internal consistency check used by the test suite and smoke runs.

    Kept out of the import path on purpose — this module is definition-only and must
    not perform work at import time.
    """
    for key, decision in policy.items():
        if not isinstance(key, str) or not key:
            raise ValueError(f"policy key must be a non-empty str, got {key!r}")
        if decision not in _VALID_DECISIONS:
            raise ValueError(f"policy decision for {key!r} must be one of {_VALID_DECISIONS}, got {decision!r}")
