"""Community blueprint helpers for reviewer reputation presentation."""

from flask_login import current_user

from twitclone.community import community_blueprint
from twitclone.reviewer_reputation import reviewer_reputation


@community_blueprint.context_processor
def inject_reviewer_reputation():
    if not current_user.is_authenticated:
        return {"current_reviewer_reputation": None}
    return {"current_reviewer_reputation": reviewer_reputation(current_user.id)}


__all__ = []
