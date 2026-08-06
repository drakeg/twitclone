"""Timeline Blueprint."""

from flask import Blueprint

timeline_blueprint = Blueprint("timeline", __name__)

from twitclone.timeline import routes  # noqa: E402, F401

__all__ = ["timeline_blueprint"]
