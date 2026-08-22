"""Repeatable filesystem-to-object-storage media migration."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from twitclone.media_storage import MediaNotFound


@dataclass(frozen=True)
class MediaMigrationResult:
    discovered: int = 0
    copied: int = 0
    unchanged: int = 0
    conflicts: int = 0
    bytes_copied: int = 0


def _digest(content: bytes) -> bytes:
    return hashlib.sha256(content).digest()


def migrate_media_directory(source, destination, *, dry_run=False, overwrite=False):
    """Copy safe regular files, verifying every destination object by content."""
    source = Path(source)
    if not source.is_dir():
        raise ValueError(f"Media source directory does not exist: {source}")

    discovered = copied = unchanged = conflicts = bytes_copied = 0
    for path in sorted(source.iterdir(), key=lambda item: item.name):
        if path.is_symlink() or not path.is_file() or path.name.startswith("."):
            continue
        discovered += 1
        content = path.read_bytes()
        try:
            current = destination.get(path.name).content
        except MediaNotFound:
            current = None

        if current is not None and _digest(current) == _digest(content):
            unchanged += 1
            continue
        if current is not None and not overwrite:
            conflicts += 1
            continue
        if not dry_run:
            destination.put(path.name, content)
            verified = destination.get(path.name).content
            if _digest(verified) != _digest(content):
                raise RuntimeError(f"Destination verification failed for {path.name}")
        copied += 1
        bytes_copied += len(content)

    return MediaMigrationResult(
        discovered=discovered,
        copied=copied,
        unchanged=unchanged,
        conflicts=conflicts,
        bytes_copied=bytes_copied,
    )


__all__ = ["MediaMigrationResult", "migrate_media_directory"]
