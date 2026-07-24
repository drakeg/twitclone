"""Supported TwitClone application entry point."""

import os

from config import Config
from twitclone import create_app


application = create_app()
app = application


if __name__ == "__main__":
    application.run(
        debug=Config.ENVIRONMENT == "development",
        port=int(os.getenv("PORT", "8000")),
    )
