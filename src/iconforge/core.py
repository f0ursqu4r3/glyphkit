"""Core utilities: image loading, validation, resizing."""

from __future__ import annotations

import pathlib

from PIL import Image


class IconforgeError(Exception):
    """Base exception for iconforge errors."""


def resize_image(source: Image.Image, size: int) -> Image.Image:
    """Resize source image to size×size using LANCZOS resampling."""
    return source.resize((size, size), Image.LANCZOS)


def load_and_validate_image(path: pathlib.Path) -> Image.Image:
    """Load image, validate it is square PNG. Warn if under 1024×1024."""
    if not path.exists():
        raise IconforgeError(f"File not found: {path}")
    if path.suffix.lower() != ".png":
        raise IconforgeError(f"Unsupported format: {path.suffix}. Only PNG is supported.")
    img = Image.open(path)
    w, h = img.size
    if w != h:
        raise IconforgeError(f"Image must be square, got {w}×{h}")
    if w < 1024:
        import warnings
        warnings.warn(f"Source image is {w}×{h}, 1024×1024 recommended for best quality")
    return img


def has_transparency(image: Image.Image) -> bool:
    """Check if image has an alpha channel with any non-opaque pixels."""
    if image.mode != "RGBA":
        return False
    alpha = image.getchannel("A")
    return alpha.getextrema()[0] < 255
