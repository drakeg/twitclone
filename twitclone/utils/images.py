"""Image processing helpers."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


def resize_image(
    image_path: str | Path,
    output_path: str | Path,
    size: tuple[int, int] = (200, 200),
) -> None:
    """Create a thumbnail using the existing aspect-preserving behavior."""
    with Image.open(image_path) as image:
        image.thumbnail(size)
        image.save(output_path)
