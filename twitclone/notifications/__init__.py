"""Notifications Blueprint."""

from flask import Blueprint

notifications_blueprint = Blueprint("notifications", __name__)

from twitclone.notifications import routes  # noqa: E402, F401

__all__ = ["notifications_blueprint"]
