"""Supported TwitClone application entry point.

Use this module for local execution and WSGI deployment so environment-backed
configuration is applied consistently while the legacy monolith is stabilized.
"""

from pathlib import Path

from config import Config
from app import app, scheduler


app.config.from_object(Config)
Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

if not app.config["SCHEDULER_ENABLED"] and scheduler.running:
    scheduler.shutdown(wait=False)

application = app


if __name__ == "__main__":
    app.run(
        debug=Config.ENVIRONMENT == "development",
        port=int(__import__("os").getenv("PORT", "8000")),
    )
