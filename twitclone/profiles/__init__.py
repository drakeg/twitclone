"""Profiles and social graph Blueprint."""

from flask import Blueprint

profiles_blueprint = Blueprint("profiles", __name__)

from twitclone.profiles import routes  # noqa: E402, F401

__all__ = ["profiles_blueprint"]
