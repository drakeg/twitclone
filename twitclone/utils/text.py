"""Text formatting helpers."""

from __future__ import annotations

import re


def make_clickable_links(text: str) -> str:
    """Convert @mentions and #hashtags to the existing profile/hashtag links."""
    text = re.sub(r"@(\w+)", r'<a href="/profile/\1">@\1</a>', text)
    return re.sub(r"#(\w+)", r'<a href="/hashtag/\1">#\1</a>', text)
