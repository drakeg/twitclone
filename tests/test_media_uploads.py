"""Secure media-upload boundary tests."""

from io import BytesIO
from pathlib import Path
import re

from PIL import Image

from twitclone.extensions import db
from twitclone.models import Tweet, User
from twitclone.timeline.media import IMAGE_UPLOAD_MAX_BYTES


def log_in(client, app):
    with app.app_context():
        user = User(username="alice", email="alice@example.com", password="hash")
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def png_bytes():
    payload = BytesIO()
    Image.new("RGB", (20, 20), "red").save(payload, format="PNG")
    return payload.getvalue()


def test_valid_image_uses_generated_filename(client, app):
    log_in(client, app)

    response = client.post(
        "/tweet",
        data={"content": "photo", "image": (BytesIO(png_bytes()), "my photo.png", "image/png")},
    )

    assert response.status_code == 302
    with app.app_context():
        filename = Tweet.query.one().image
        upload_folder = Path(app.config["UPLOAD_FOLDER"])
    assert re.fullmatch(r"thumb_[0-9a-f]{32}\.png", filename)
    assert (upload_folder / filename).is_file()
    assert (upload_folder / filename.removeprefix("thumb_")).is_file()


def assert_rejected(client, app, image):
    response = client.post("/tweet", data={"content": "photo", "image": image})
    assert response.status_code == 302
    with app.app_context():
        assert Tweet.query.count() == 0


def test_rejects_disallowed_extension(client, app):
    log_in(client, app)
    assert_rejected(client, app, (BytesIO(png_bytes()), "image.svg", "image/svg+xml"))


def test_rejects_mismatched_mime_type(client, app):
    log_in(client, app)
    assert_rejected(client, app, (BytesIO(png_bytes()), "image.png", "image/jpeg"))


def test_rejects_invalid_image_content(client, app):
    log_in(client, app)
    assert_rejected(client, app, (BytesIO(b"not an image"), "image.png", "image/png"))


def test_rejects_content_that_mismatches_extension(client, app):
    log_in(client, app)
    assert_rejected(client, app, (BytesIO(png_bytes()), "image.jpg", "image/jpeg"))


def test_rejects_image_above_size_limit(client, app):
    log_in(client, app)
    assert_rejected(
        client,
        app,
        (BytesIO(b"x" * (IMAGE_UPLOAD_MAX_BYTES + 1)), "image.png", "image/png"),
    )
