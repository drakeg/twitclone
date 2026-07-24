"""Stable import boundary for TwitClone Flask extensions.

This module is the supported import location for shared Flask extension objects.
During the incremental monolith refactor, the objects are still initialized by
``app.py``. Later Sprint 2 work will move their definitions here without
requiring models, migrations, tests, and routes to change imports again.
"""

from __future__ import annotations

from typing import Any

_EXTENSION_NAMES = {
    "db",
    "migrate",
    "bcrypt",
    "login_manager",
    "csrf",
}


def __getattr__(name: str) -> Any:
    """Return the extension object currently owned by the legacy module."""

    if name not in _EXTENSION_NAMES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    import app as legacy_app

    return getattr(legacy_app, name)


def __dir__() -> list[str]:
    """Expose supported extension names to interactive tooling."""

    return sorted(set(globals()) | _EXTENSION_NAMES)


__all__ = sorted(_EXTENSION_NAMES)
