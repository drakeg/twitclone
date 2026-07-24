"""Shared, application-independent Flask extension objects."""

from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

# Extensions are intentionally created without an application. The configured
# application initializes them after configuration has been loaded and validated.
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "login"
csrf = CSRFProtect()


def init_extensions(app) -> None:
    """Bind all shared extensions to a configured Flask application."""

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)


__all__ = [
    "bcrypt",
    "csrf",
    "db",
    "init_extensions",
    "login_manager",
    "migrate",
]
