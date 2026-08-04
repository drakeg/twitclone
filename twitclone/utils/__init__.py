"""Package-owned utility boundary and legacy compatibility binding."""

from __future__ import annotations

from types import ModuleType

from twitclone.utils.gravatar import gravatar
from twitclone.utils.hashtags import get_newest_users, get_trending_hashtags
from twitclone.utils.images import resize_image
from twitclone.utils.text import make_clickable_links


def bind_legacy_module(module: ModuleType) -> None:
    """Point the transitional legacy module at package-owned helpers.

    Routes and template callbacks resolve these names at request time, so rebinding
    preserves their public endpoints while making the package implementations
    authoritative on the supported application-factory path.
    """
    module.gravatar = gravatar
    module.get_newest_users = get_newest_users
    module.get_trending_hashtags = get_trending_hashtags
    module.resize_image = resize_image
    module.make_clickable_links = make_clickable_links


__all__ = [
    "bind_legacy_module",
    "get_newest_users",
    "get_trending_hashtags",
    "gravatar",
    "make_clickable_links",
    "resize_image",
]
