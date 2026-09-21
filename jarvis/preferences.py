"""Jarvis personal preferences — user defaults for how Jarvis should behave.

Static definition only. This module must not perform any runtime work on import
and is intentionally distinct from jarvis.instructions (behavioral guardrails).

Preferences describe default user choices (communication style, coding approach,
tool execution preference, workflow style). Instructions describe how Jarvis should
work. The two are kept separate on purpose.
"""

from __future__ import annotations

# Category → preference key → default value. All values are the defaults already
# established for Jarvis; callers that need user overrides consume this shape and
# merge it with external config/prompt sources in a later task.
PREFERENCES: dict[str, dict[str, object]] = {
    "communication": {
        "concise": True,
    },
    "coding": {
        "understand_existing_code_first": True,
    },
    "tools": {
        "prefer_local_execution": True,
    },
    "workflow": {
        "prefer_simple_solution": True,
    },
}

# Convenience accessor for prompt/config integration without guessing the top-level
# field name.
USER_PREFERENCES: dict[str, dict[str, object]] = PREFERENCES
