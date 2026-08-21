"""Secure media-upload boundary tests."""

from io import BytesIO
from pathlib import Path
import re

from PIL import Image
import pytest
from werkzeug.datastructures import FileStorage

from twitclone.extensions import db
from twitclone.models import Tweet, User
from twitclone.timeline.media import IMAGE_UPLOAD_MAX_BYTES
from twitclone.timeline.media import store_image_upload
from twitclone.media_storage import S3MediaStorage


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
        tweet = Tweet.query.one()
        filename = tweet.image
        original_filename = tweet.original_image
        upload_folder = Path(app.config["UPLOAD_FOLDER"])
    assert re.fullmatch(r"thumb_[0-9a-f]{32}\.png", filename)
    assert re.fullmatch(r"original_[0-9a-f]{32}\.png", original_filename)
    assert (upload_folder / filename).is_file()
    assert (upload_folder / original_filename).is_file()
    assert filename.removeprefix("thumb_") == original_filename.removeprefix("original_")
    served = client.get(f"/uploads/{filename}")
    assert served.status_code == 200
    assert served.mimetype == "image/png"
    assert served.data.startswith(b"\x89PNG")
    assert client.get(f"/uploads/{original_filename}").status_code == 404


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


def test_processing_failure_cleans_up_partial_files(tmp_path, monkeypatch):
    upload = FileStorage(
        stream=BytesIO(png_bytes()), filename="image.png", content_type="image/png"
    )

    def fail_resize(*args, **kwargs):
        raise OSError("thumbnail failure")

    monkeypatch.setattr("twitclone.timeline.media.resize_image", fail_resize)
    with pytest.raises(OSError, match="thumbnail failure"):
        store_image_upload(upload, tmp_path)

    assert list(tmp_path.iterdir()) == []


class FakeBody:
    def __init__(self, content): self.content = content
    def read(self): return self.content


class FakeS3Client:
    def __init__(self): self.objects = {}
    def put_object(self, **kwargs): self.objects[(kwargs["Bucket"], kwargs["Key"])] = (kwargs["Body"], kwargs["ContentType"])
    def get_object(self, **kwargs):
        content, content_type = self.objects[(kwargs["Bucket"], kwargs["Key"])]
        return {"Body": FakeBody(content), "ContentType": content_type}
    def delete_object(self, **kwargs): self.objects.pop((kwargs["Bucket"], kwargs["Key"]), None)


def test_s3_adapter_keeps_media_private_behind_existing_name_contract():
    client = FakeS3Client()
    storage = S3MediaStorage(bucket="ripple-media", region="nyc3", prefix="production/media", client=client)
    storage.put("thumb_example.png", b"image-bytes", content_type="image/png")
    assert client.objects[("ripple-media", "production/media/thumb_example.png")] == (b"image-bytes", "image/png")
    media = storage.get("thumb_example.png")
    assert media.content == b"image-bytes"
    assert media.content_type == "image/png"
    storage.delete("thumb_example.png")
    assert client.objects == {}


@pytest.mark.parametrize("name", ["../secret", "folder/image.png", "", "."])
def test_s3_adapter_rejects_unsafe_object_names(name):
    storage = S3MediaStorage(bucket="ripple-media", region="nyc3", client=FakeS3Client())
    with pytest.raises(ValueError, match="safe path component"):
        storage.put(name, b"content")
