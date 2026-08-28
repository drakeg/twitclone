"""Collaborative knowledge resource surfaces."""

from flask import Blueprint

resources_blueprint = Blueprint("resources", __name__, url_prefix="/resources")

from twitclone.resources import routes  # noqa: E402,F401

__all__ = ["resources_blueprint"]
