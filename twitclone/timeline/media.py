"""Secure image-upload validation and filename generation."""

from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

from twitclone.utils.images import resize_image

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


def store_image_upload(upload, upload_folder):
    """Validate and store distinct original and thumbnail files."""
    error, generated_name = prepare_image_upload(upload)
    if error:
        return error, None, None

    folder = Path(upload_folder)
    original_name = f"original_{generated_name}"
    thumbnail_name = f"thumb_{generated_name}"
    original_path = folder / original_name
    thumbnail_path = folder / thumbnail_name
    try:
        upload.save(original_path)
        resize_image(original_path, thumbnail_path)
    except Exception:
        original_path.unlink(missing_ok=True)
        thumbnail_path.unlink(missing_ok=True)
        raise
    return None, original_name, thumbnail_name


__all__ = ["IMAGE_UPLOAD_MAX_BYTES", "prepare_image_upload", "store_image_upload"]
