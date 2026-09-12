"""Versioned public API surface for Ripple."""

from flask import Blueprint


api_blueprint = Blueprint("api_v1", __name__, url_prefix="/api/v1")

from twitclone.api import routes as _routes  # noqa: E402,F401


__all__ = ["api_blueprint"]
