"""Administrative and verification workflows."""

from flask import Blueprint

admin_blueprint = Blueprint("admin", __name__)

from twitclone.admin import routes  # noqa: E402,F401
from twitclone.admin import fact_context  # noqa: E402,F401

__all__ = ["admin_blueprint"]
