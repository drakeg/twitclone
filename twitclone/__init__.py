"""TwitClone application factory.

This factory provides one supported construction path while ``app.py`` remains
as a transitional startup and compatibility module.
"""

from __future__ import annotations

from pathlib import Path

from flask import Flask

from config import Config


def create_app(config_object: type[Config] = Config) -> Flask:
    """Create and configure the TwitClone Flask application.

    The legacy module still owns route registration. Importing it only after
    configuration validation ensures the supported startup path fails before
    serving requests when required environment values are missing.
    """

    config_object.validate()

    # Imported lazily so callers can establish environment variables before the
    # legacy module and its Flask extensions are loaded.
    import app as legacy_app

    from twitclone.auth import auth_blueprint
    from twitclone.bookmarks import bookmarks_blueprint
    from twitclone.discovery import discovery_blueprint
    from twitclone.messaging import messaging_blueprint
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

    if auth_blueprint.name not in flask_app.blueprints:
        flask_app.register_blueprint(auth_blueprint)
    if timeline_blueprint.name not in flask_app.blueprints:
        flask_app.register_blueprint(timeline_blueprint)
    if messaging_blueprint.name not in flask_app.blueprints:
        flask_app.register_blueprint(messaging_blueprint)
    if polls_blueprint.name not in flask_app.blueprints:
        flask_app.register_blueprint(polls_blueprint)
    if notifications_blueprint.name not in flask_app.blueprints:
        flask_app.register_blueprint(notifications_blueprint)
    if profiles_blueprint.name not in flask_app.blueprints:
        flask_app.register_blueprint(profiles_blueprint)
    if discovery_blueprint.name not in flask_app.blueprints:
        flask_app.register_blueprint(discovery_blueprint)
    if bookmarks_blueprint.name not in flask_app.blueprints:
        flask_app.register_blueprint(bookmarks_blueprint)

    if not flask_app.config["SCHEDULER_ENABLED"] and scheduler.running:
        scheduler.shutdown(wait=False)

    return flask_app


__all__ = ["create_app"]
