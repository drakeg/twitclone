"""Bookmarks Blueprint."""

from flask import Blueprint

bookmarks_blueprint = Blueprint("bookmarks", __name__)

from twitclone.bookmarks import routes  # noqa: E402, F401

__all__ = ["bookmarks_blueprint"]
