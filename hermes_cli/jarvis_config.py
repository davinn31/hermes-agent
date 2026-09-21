"""Jarvis Personal Layer config integration — resolved config accessor.

Minimal wrapper around Hermes's config loaders so callers can read the resolved
``jarvis`` section without importing the static ``jarvis.*`` definition modules here.
The definition layer (identity/instructions/preferences/security) stays the source of
truth; config is the activation/override surface only.
"""

from __future__ import annotations

from typing import Any, Dict

from hermes_cli.config import load_config_readonly


def get_jarvis_section(*, effective: bool = False) -> Dict[str, Any]:
    """Return the resolved ``jarvis`` config section, or ``{}`` when absent/malformed.

    *effective* selects the loader that applies managed overlays + env expansion
    (gateway-runtime shape). Default uses the CLI-style merged loader.
    """
    cfg: Dict[str, Any] = load_config_readonly()
    section = cfg.get("jarvis")
    if not isinstance(section, dict):
        return {}
    return section
