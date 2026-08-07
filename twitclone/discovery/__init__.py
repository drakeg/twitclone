"""Discovery Blueprint."""

from flask import Blueprint

discovery_blueprint = Blueprint("discovery", __name__)

from twitclone.discovery import routes  # noqa: E402, F401

__all__ = ["discovery_blueprint"]
