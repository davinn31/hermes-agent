"""Jarvis Personal Layer — composition of identity, instructions, preferences, and security policy.

Composition only. No memory, no prompt assembly, no enforcement, no persistence.
All four components are reused directly from their definition modules; this module
does not duplicate or transform their data."""

from __future__ import annotations

from dataclasses import dataclass, field

from jarvis.identity import IDENTITY
from jarvis.instructions import INSTRUCTIONS
from jarvis.preferences import USER_PREFERENCES
from jarvis.security import SECURITY_POLICY


@dataclass(frozen=True)
class JarvisPersonalLayer:
    """Static composition of the Jarvis Personal Layer components.

    Each field holds a direct reference to the corresponding definition
    module's public constant — not a copy. Callers that need the whole layer
    use this class; callers that only need one component can still import the
    definition modules directly.
    """

    identity: dict[str, str] = field(default_factory=lambda: IDENTITY)
    instructions: tuple[str, ...] = field(default_factory=lambda: INSTRUCTIONS)
    preferences: dict[str, dict[str, object]] = field(default_factory=lambda: USER_PREFERENCES)
    security_policy: dict[str, dict[str, str]] = field(default_factory=lambda: SECURITY_POLICY)


# Module-level convenience accessor, mirroring the accessor shape already used
# by jarvis.identity (IDENTITY), jarvis.instructions (INSTRUCTIONS), jarvis.preferences
# (USER_PREFERENCES), and jarvis.security (POLICY).
PERSONAL_LAYER = JarvisPersonalLayer()
