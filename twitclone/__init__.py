"""TwitClone application factory.

This factory provides one supported construction path while the existing routes
remain in the legacy ``app.py`` module. Later Sprint 2 stories will move those
responsibilities into this package incrementally.
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

    from twitclone.utils import bind_legacy_module
    from twitclone.auth import auth_blueprint

    bind_legacy_module(legacy_app)

    flask_app = legacy_app.app
    scheduler = legacy_app.scheduler

    flask_app.config.from_object(config_object)
    Path(flask_app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    if auth_blueprint.name not in flask_app.blueprints:
        flask_app.register_blueprint(auth_blueprint)

    if not flask_app.config["SCHEDULER_ENABLED"] and scheduler.running:
        scheduler.shutdown(wait=False)

    return flask_app


__all__ = ["create_app"]
