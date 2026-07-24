"""Regression tests for package-owned Flask extension objects."""

from pathlib import Path


def test_shared_extension_imports_reference_active_objects():
    import app as legacy_app
    from twitclone import extensions

    assert extensions.db is legacy_app.db
    assert extensions.migrate is legacy_app.migrate
    assert extensions.bcrypt is legacy_app.bcrypt
    assert extensions.login_manager is legacy_app.login_manager
    assert extensions.csrf is legacy_app.csrf


def test_database_extension_is_registered_with_application():
    import app as legacy_app
    from twitclone.extensions import db

    assert "sqlalchemy" in legacy_app.app.extensions
    assert legacy_app.app.extensions["sqlalchemy"] is not None
    assert db.Model.metadata.tables


def test_legacy_module_does_not_construct_extensions():
    source = Path("app.py").read_text(encoding="utf-8")

    assert "SQLAlchemy(" not in source
    assert "Migrate(" not in source
    assert "Bcrypt(" not in source
    assert "LoginManager(" not in source
    assert "CSRFProtect(" not in source
    assert "init_extensions(app)" in source


def test_login_manager_keeps_existing_login_view():
    from twitclone.extensions import login_manager

    assert login_manager.login_view == "login"
