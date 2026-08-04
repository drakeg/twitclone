"""Gravatar URL helpers."""

from __future__ import annotations

import hashlib


def gravatar(email: str, size: int = 100, default: str = "identicon", rating: str = "g") -> str:
    """Return the Gravatar URL used by existing templates."""
    digest = hashlib.md5(email.lower().encode("utf-8")).hexdigest()
    return f"https://www.gravatar.com/avatar/{digest}?s={size}&d={default}&r={rating}"
