"""Filesystem and private S3-compatible media storage adapters."""

from __future__ import annotations

from dataclasses import dataclass
import mimetypes
from pathlib import Path, PurePosixPath

from flask import current_app


class MediaNotFound(FileNotFoundError):
    """Raised when a requested media object does not exist."""


@dataclass(frozen=True)
class StoredMedia:
    content: bytes
    content_type: str


def _safe_name(name: str) -> str:
    candidate = PurePosixPath(name)
    if not name or candidate.name != name or name in {".", ".."}:
        raise ValueError("Media names must be a single safe path component")
    return name


def _content_type(name: str) -> str:
    return mimetypes.guess_type(name)[0] or "application/octet-stream"


class FileSystemMediaStorage:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, name: str, content: bytes, *, content_type: str | None = None) -> None:
        (self.root / _safe_name(name)).write_bytes(content)

    def get(self, name: str) -> StoredMedia:
        path = self.root / _safe_name(name)
        try:
            return StoredMedia(path.read_bytes(), _content_type(name))
        except FileNotFoundError as exc:
            raise MediaNotFound(name) from exc

    def delete(self, name: str) -> None:
        (self.root / _safe_name(name)).unlink(missing_ok=True)


class S3MediaStorage:
    def __init__(self, *, bucket, region, endpoint_url=None, prefix="media", client=None):
        if client is None:
            import boto3

            client = boto3.client("s3", region_name=region, endpoint_url=endpoint_url)
        self.client = client
        self.bucket = bucket
        self.prefix = prefix.strip("/")

    def _key(self, name: str) -> str:
        safe_name = _safe_name(name)
        return f"{self.prefix}/{safe_name}" if self.prefix else safe_name

    def put(self, name: str, content: bytes, *, content_type: str | None = None) -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=self._key(name),
            Body=content,
            ContentType=content_type or _content_type(name),
        )

    def get(self, name: str) -> StoredMedia:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=self._key(name))
        except Exception as exc:
            code = str(getattr(exc, "response", {}).get("Error", {}).get("Code", ""))
            if code in {"NoSuchKey", "404", "NotFound"}:
                raise MediaNotFound(name) from exc
            raise
        return StoredMedia(
            response["Body"].read(),
            response.get("ContentType") or _content_type(name),
        )

    def delete(self, name: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=self._key(name))


def build_media_storage(config, *, client=None):
    backend = config.get("MEDIA_STORAGE_BACKEND", "filesystem").lower()
    if backend == "filesystem":
        return FileSystemMediaStorage(config["UPLOAD_FOLDER"])
    if backend == "s3":
        return S3MediaStorage(
            bucket=config["MEDIA_S3_BUCKET"],
            region=config["MEDIA_S3_REGION"],
            endpoint_url=config.get("MEDIA_S3_ENDPOINT_URL"),
            prefix=config.get("MEDIA_S3_PREFIX", "media"),
            client=client,
        )
    raise RuntimeError(f"Unsupported MEDIA_STORAGE_BACKEND: {backend}")


def init_media_storage(app) -> None:
    app.extensions["media_storage"] = build_media_storage(app.config)


def get_media_storage():
    return current_app.extensions["media_storage"]


__all__ = [
    "FileSystemMediaStorage",
    "MediaNotFound",
    "S3MediaStorage",
    "StoredMedia",
    "build_media_storage",
    "get_media_storage",
    "init_media_storage",
]
