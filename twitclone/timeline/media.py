"""Secure image-upload validation and filename generation."""

from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

IMAGE_UPLOAD_MAX_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    ".gif": ("image/gif", "GIF"),
    ".jpg": ("image/jpeg", "JPEG"),
    ".jpeg": ("image/jpeg", "JPEG"),
    ".png": ("image/png", "PNG"),
}


def prepare_image_upload(upload):
    extension = Path(upload.filename or "").suffix.lower()
    expected = ALLOWED_IMAGE_TYPES.get(extension)
    if expected is None:
        return "Image must be a PNG, JPEG, or GIF file.", None
    expected_mimetype, expected_format = expected
    if upload.mimetype != expected_mimetype:
        return "Image type does not match its file extension.", None

    payload = upload.stream.read(IMAGE_UPLOAD_MAX_BYTES + 1)
    upload.stream.seek(0)
    if len(payload) > IMAGE_UPLOAD_MAX_BYTES:
        return "Image exceeds the 5 MB size limit.", None

    try:
        with Image.open(BytesIO(payload)) as candidate:
            detected_format = candidate.format
            candidate.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        return "Uploaded file is not a valid image.", None
    if detected_format != expected_format:
        return "Image content does not match its file extension.", None

    return None, f"{uuid4().hex}{extension}"


__all__ = ["IMAGE_UPLOAD_MAX_BYTES", "prepare_image_upload"]
