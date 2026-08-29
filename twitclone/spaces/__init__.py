"""Persistent community/topic spaces."""

from flask import Blueprint

spaces_blueprint = Blueprint("spaces", __name__, url_prefix="/spaces")

from twitclone.spaces import routes  # noqa: E402,F401

__all__ = ["spaces_blueprint"]
