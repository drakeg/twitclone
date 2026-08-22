from twitclone.extensions import bcrypt, db
from twitclone.models import User


def create_user(app, *, username, email, password="secret"):
    with app.app_context():
        user = User(
            username=username,
            email=email,
            password=bcrypt.generate_password_hash(password).decode("utf-8"),
        )
        db.session.add(user)
        db.session.commit()


def login(client, *, email, password="secret"):
    return client.post("/login", data={"email": email, "password": password})


def test_invalid_login_connects_error_summary_to_fields(client):
    response = client.post(
        "/login", data={"email": "missing@example.com", "password": "wrong"}
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'id="login-error" role="alert" tabindex="-1" data-error-summary' in html
    assert html.count('aria-invalid="true" aria-describedby="login-error"') == 2
    assert 'value="missing@example.com"' in html
    assert 'name="password" value=' not in html


def test_registration_errors_preserve_safe_values_and_identify_fields(client, app):
    data = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "secret",
        "community_standards": "yes",
    }
    assert client.post("/register", data=data).status_code == 302

    response = client.post("/register", data=data)
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'id="register-error" role="alert" tabindex="-1" data-error-summary' in html
    assert html.count('aria-invalid="true" aria-describedby="register-error"') == 2
    assert 'value="alice"' in html
    assert 'value="alice@example.com"' in html


def test_standards_error_identifies_only_the_checkbox(client):
    response = client.post(
        "/register",
        data={"username": "alice", "email": "alice@example.com", "password": "secret"},
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert html.count('aria-invalid="true" aria-describedby="register-error"') == 1
    assert 'id="community_standards"' in html


def test_shell_exposes_one_polite_interaction_status_channel(client):
    html = client.get("/").get_data(as_text=True)

    assert html.count('id="interaction-status"') == 1
    assert 'id="interaction-status" role="status" aria-live="polite" aria-atomic="true"' in html
    assert "could not be completed" in html
    assert "You are now following" in html


def test_composer_exposes_character_and_image_status(client):
    html = client.get("/").get_data(as_text=True)

    assert 'aria-describedby="content-limit"' in html
    assert 'id="content-limit" role="status" aria-live="polite" aria-atomic="true"' in html
    assert 'id="imagePreview" role="status" aria-live="polite" aria-atomic="true"' in html
    assert "postContent.addEventListener('input', updateContentLimit)" in html


def test_follow_buttons_share_one_toggle_handler_and_expose_pressed_state(client, app):
    create_user(app, username="alice", email="alice@example.com")
    create_user(app, username="bob", email="bob@example.com")
    assert login(client, email="alice@example.com").status_code == 302

    search = client.post("/search", data={"search_query": "bob"})
    profile = client.get("/profile/bob")
    search_html = search.get_data(as_text=True)
    profile_html = profile.get_data(as_text=True)

    assert search_html.count("querySelectorAll('.follow-btn')") == 1
    assert 'data-username="bob" data-action="follow" aria-pressed="false"' in search_html
    assert 'id="follow-btn"' in profile_html
    assert 'data-username="bob" data-action="follow" aria-pressed="false"' in profile_html
    assert "setAttribute('aria-pressed', String(nowFollowing))" in profile_html
