"""Secure image-upload validation and filename generation."""

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

from twitclone.utils.images import resize_image
from twitclone.media_storage import FileSystemMediaStorage

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


def _storage_adapter(storage):
    return storage if hasattr(storage, "put") else FileSystemMediaStorage(storage)


def store_image_upload(upload, storage):
    """Validate and store distinct original and thumbnail files."""
    error, generated_name = prepare_image_upload(upload)
    if error:
        return error, None, None

    storage = _storage_adapter(storage)
    original_name = f"original_{generated_name}"
    thumbnail_name = f"thumb_{generated_name}"
    with TemporaryDirectory() as temporary_folder:
        original_path = Path(temporary_folder) / original_name
        thumbnail_path = Path(temporary_folder) / thumbnail_name
        upload.save(original_path)
        resize_image(original_path, thumbnail_path)
        try:
            storage.put(original_name, original_path.read_bytes())
            storage.put(thumbnail_name, thumbnail_path.read_bytes())
        except Exception:
            storage.delete(original_name)
            storage.delete(thumbnail_name)
            raise
    return None, original_name, thumbnail_name


def store_profile_banner(upload, storage):
    error, generated_name = prepare_image_upload(upload)
    if error:
        return error, None
    banner_name = f"banner_{generated_name}"
    storage = _storage_adapter(storage)
    storage.put(banner_name, upload.stream.read())
    upload.stream.seek(0)
    return None, banner_name


__all__ = ["IMAGE_UPLOAD_MAX_BYTES", "prepare_image_upload", "store_image_upload", "store_profile_banner"]
