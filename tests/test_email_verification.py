"""Regression coverage for email ownership verification."""

from datetime import UTC, datetime

from twitclone.auth.recovery import generate_email_verification_token
from twitclone.auth.verification import EmailVerificationStatus, is_email_verified
from twitclone.extensions import bcrypt, db
from twitclone.models import User


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _create_user(app, *, verified_status=None):
    with app.app_context():
        user = User(
            username="alice",
            email="alice@example.com",
            password=bcrypt.generate_password_hash("Passw0rd!").decode("utf-8"),
        )
        db.session.add(user)
        db.session.flush()
        if verified_status is not None:
            db.session.add(EmailVerificationStatus(user_id=user.id, verified_at=verified_status))
        db.session.commit()
        return user.id


def test_registration_creates_explicit_unverified_email_status(client, app):
    response = client.post(
        "/register",
        data={
            "username": "newuser",
            "email": "new@example.com",
            "password": "Passw0rd!",
            "community_standards": "yes",
        },
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"

    with app.app_context():
        user = User.query.filter_by(email="new@example.com").one()
        status = db.session.get(EmailVerificationStatus, user.id)
        assert status is not None
        assert status.verified_at is None
        assert is_email_verified(user) is False


def test_valid_verification_link_marks_email_verified(client, app):
    user_id = _create_user(app, verified_status=None)
    with app.app_context():
        user = db.session.get(User, user_id)
        db.session.add(EmailVerificationStatus(user_id=user.id))
        db.session.commit()
        token = generate_email_verification_token(user.email, user.password)

    response = client.get(f"/verify-email/{token}")
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"

    with app.app_context():
        user = db.session.get(User, user_id)
        status = db.session.get(EmailVerificationStatus, user_id)
        assert status.verified_at is not None
        assert is_email_verified(user) is True


def test_verification_link_is_invalidated_by_password_change(client, app):
    user_id = _create_user(app, verified_status=None)
    with app.app_context():
        user = db.session.get(User, user_id)
        db.session.add(EmailVerificationStatus(user_id=user.id))
        db.session.commit()
        token = generate_email_verification_token(user.email, user.password)
        user.password = bcrypt.generate_password_hash("Different1!").decode("utf-8")
        db.session.commit()

    response = client.get(f"/verify-email/{token}")
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"
    with app.app_context():
        assert db.session.get(EmailVerificationStatus, user_id).verified_at is None


def test_unverified_user_sees_resend_control_and_cannot_request_identity_verification(client, app):
    user_id = _create_user(app, verified_status=None)
    with app.app_context():
        db.session.add(EmailVerificationStatus(user_id=user_id))
        db.session.commit()
    _login(client, user_id)

    profile = client.get("/profile/alice")
    assert profile.status_code == 200
    assert b"Verify your email address." in profile.data
    assert b"Resend verification email" in profile.data

    verification = client.get("/verification/apply")
    assert verification.status_code == 302
    assert verification.headers["Location"].endswith("/profile/alice")


def test_resend_keeps_account_unverified_until_link_is_used(client, app):
    user_id = _create_user(app, verified_status=None)
    with app.app_context():
        db.session.add(EmailVerificationStatus(user_id=user_id))
        db.session.commit()
    _login(client, user_id)

    response = client.post("/resend-verification")
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(EmailVerificationStatus, user_id).verified_at is None


def test_legacy_user_without_status_row_remains_verified(client, app):
    user_id = _create_user(app)
    with app.app_context():
        user = db.session.get(User, user_id)
        assert db.session.get(EmailVerificationStatus, user_id) is None
        assert is_email_verified(user) is True
    _login(client, user_id)

    response = client.get("/verification/apply")
    assert response.status_code == 200


def test_changing_verified_email_requires_reverification(client, app):
    verified_at = datetime.now(UTC).replace(tzinfo=None)
    user_id = _create_user(app, verified_status=verified_at)
    _login(client, user_id)

    response = client.post(
        "/profile/edit",
        data={"username": "alice", "email": "new@example.com", "bio": "updated"},
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/profile/alice"
    with app.app_context():
        user = db.session.get(User, user_id)
        status = db.session.get(EmailVerificationStatus, user_id)
        assert user.email == "new@example.com"
        assert status.verified_at is None
        assert is_email_verified(user) is False


def test_profile_edit_with_same_email_preserves_verification(client, app):
    verified_at = datetime.now(UTC).replace(tzinfo=None)
    user_id = _create_user(app, verified_status=verified_at)
    _login(client, user_id)

    response = client.post(
        "/profile/edit",
        data={"username": "alice", "email": "alice@example.com", "bio": "updated"},
    )

    assert response.status_code == 302
    with app.app_context():
        status = db.session.get(EmailVerificationStatus, user_id)
        assert status.verified_at == verified_at


def test_profile_email_cannot_change_to_another_accounts_address(client, app):
    verified_at = datetime.now(UTC).replace(tzinfo=None)
    user_id = _create_user(app, verified_status=verified_at)
    with app.app_context():
        db.session.add(User(username="bob", email="bob@example.com", password="hash"))
        db.session.commit()
    _login(client, user_id)

    response = client.post(
        "/profile/edit",
        data={"username": "alice", "email": "bob@example.com", "bio": "updated"},
    )

    assert response.status_code == 200
    assert b"already registered to another Ripple account" in response.data
    with app.app_context():
        user = db.session.get(User, user_id)
        status = db.session.get(EmailVerificationStatus, user_id)
        assert user.email == "alice@example.com"
        assert status.verified_at == verified_at
