"""Authentication Blueprint."""

from flask import Blueprint

auth_blueprint = Blueprint("auth", __name__)

from twitclone.auth import routes  # noqa: E402, F401

__all__ = ["auth_blueprint"]
