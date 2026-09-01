"""Public reply routes."""

from flask import Blueprint

replies_blueprint = Blueprint("replies", __name__)

from twitclone.replies import routes  # noqa: E402,F401

__all__ = ["replies_blueprint"]
