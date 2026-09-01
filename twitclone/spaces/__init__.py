"""Persistent community/topic spaces."""

from flask import Blueprint

from twitclone.spaces.contribution import build_space_contribution_context

spaces_blueprint = Blueprint("spaces", __name__, url_prefix="/spaces")


@spaces_blueprint.app_context_processor
def _space_template_context():
    return {"space_contribution_context": build_space_contribution_context}


from twitclone.spaces import routes  # noqa: E402,F401

__all__ = ["spaces_blueprint"]
