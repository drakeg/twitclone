"""Regression tests for the shared Flask extension import boundary."""


def test_shared_extension_imports_reference_active_objects():
    import app as legacy_app
    from twitclone.extensions import bcrypt, csrf, db, login_manager, migrate

    assert db is legacy_app.db
    assert migrate is legacy_app.migrate
    assert bcrypt is legacy_app.bcrypt
    assert login_manager is legacy_app.login_manager
    assert csrf is legacy_app.csrf


def test_database_extension_is_registered_with_application():
    import app as legacy_app
    from twitclone.extensions import db

    assert "sqlalchemy" in legacy_app.app.extensions
    assert legacy_app.app.extensions["sqlalchemy"] is not None
    assert db.Model.metadata.tables


def test_unknown_extension_name_fails_clearly():
    import pytest
    import twitclone.extensions as extensions

    with pytest.raises(AttributeError, match="has no attribute"):
        getattr(extensions, "unknown_extension")
