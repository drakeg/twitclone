"""Messaging Blueprint."""

from flask import Blueprint

messaging_blueprint = Blueprint("messaging", __name__)

from twitclone.messaging import routes  # noqa: E402, F401

__all__ = ["messaging_blueprint"]
