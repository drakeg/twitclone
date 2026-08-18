"""TwitClone application factory.

This factory provides one supported construction path while ``app.py`` remains
as a transitional startup and compatibility module.
"""

from __future__ import annotations

from pathlib import Path

import click
from flask import Flask

from config import Config


def create_app(config_object: type[Config] = Config) -> Flask:
    """Create and configure the TwitClone Flask application."""

    config_object.validate()

    import app as legacy_app

    from twitclone.admin import admin_blueprint
    from twitclone.auth import auth_blueprint
    from twitclone.bookmarks import bookmarks_blueprint
    from twitclone.discovery import discovery_blueprint
    from twitclone.extensions import db
    from twitclone.messaging import messaging_blueprint
    from twitclone.models import User
    from twitclone.notifications import notifications_blueprint
    from twitclone.observability import configure_observability
    from twitclone.polls import polls_blueprint
    from twitclone.profiles import profiles_blueprint
    from twitclone.timeline import timeline_blueprint
    from twitclone.utils import bind_legacy_module

    bind_legacy_module(legacy_app)

    flask_app = legacy_app.app
    scheduler = legacy_app.scheduler

    flask_app.config.from_object(config_object)
    Path(flask_app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    configure_observability(flask_app)

    for blueprint in (
        auth_blueprint,
        timeline_blueprint,
        messaging_blueprint,
        polls_blueprint,
        notifications_blueprint,
        profiles_blueprint,
        discovery_blueprint,
        bookmarks_blueprint,
        admin_blueprint,
    ):
        if blueprint.name not in flask_app.blueprints:
            flask_app.register_blueprint(blueprint)

    if "make-super-admin" not in flask_app.cli.commands:
        @flask_app.cli.command("make-super-admin")
        @click.argument("email")
        def make_super_admin(email):
            """Promote an existing account to Ripple super-admin by email."""
            user = User.query.filter(db.func.lower(User.email) == email.lower()).first()
            if user is None:
                raise click.ClickException("No Ripple user exists with that email address.")
            user.is_admin = True
            user.is_super_admin = True
            db.session.commit()
            click.echo(f"@{user.username} is now a Ripple super-admin.")

    if not flask_app.config["SCHEDULER_ENABLED"] and scheduler.running:
        scheduler.shutdown(wait=False)

    return flask_app


__all__ = ["create_app"]
