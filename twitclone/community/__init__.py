"""Community standards and reporting blueprint."""

from flask import Blueprint

community_blueprint = Blueprint("community", __name__)

from twitclone.community import routes  # noqa: E402,F401
from twitclone.community import reputation  # noqa: E402,F401
from twitclone.community import context_appeals  # noqa: E402,F401

__all__ = ["community_blueprint"]
