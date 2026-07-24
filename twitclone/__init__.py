"""TwitClone application factory.

This factory provides one supported construction path while the existing routes,
models, and extensions remain in the legacy ``app.py`` module. Later Sprint 2
stories will move those responsibilities into this package incrementally.
"""

from __future__ import annotations

from pathlib import Path

from flask import Flask

from config import Config


def create_app(config_object: type[Config] = Config) -> Flask:
    """Create and configure the TwitClone Flask application.

    The legacy module still owns route and model registration. Importing it only
    after configuration validation ensures the supported startup path fails
    before serving requests when required environment values are missing.
    """

    config_object.validate()

    # Imported lazily so callers can establish environment variables before the
    # legacy module and its Flask extensions are loaded.
    from app import app as flask_app
    from app import scheduler

    flask_app.config.from_object(config_object)
    Path(flask_app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    if not flask_app.config["SCHEDULER_ENABLED"] and scheduler.running:
        scheduler.shutdown(wait=False)

    return flask_app


__all__ = ["create_app"]
