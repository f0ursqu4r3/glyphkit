"""Core utilities: image loading, validation, resizing."""

from __future__ import annotations

import pathlib
import warnings

from PIL import Image
from PIL.Image import Resampling


class GlyphkitError(Exception):
    """Base exception for glyphkit errors."""


def resize_image(source: Image.Image, size: int) -> Image.Image:
    """Resize source image to size×size using LANCZOS resampling."""
    return source.resize((size, size), Resampling.LANCZOS)


def load_and_validate_image(path: pathlib.Path) -> Image.Image:
    """Load image, validate it is square PNG. Warn if under 1024×1024."""
    if not path.exists():
        raise GlyphkitError(f"File not found: {path}")
    if path.suffix.lower() != ".png":
        raise GlyphkitError(
            f"Unsupported format: {path.suffix}. Only PNG is supported."
        )
    img = Image.open(path)
    w, h = img.size
    if w != h:
        raise GlyphkitError(f"Image must be square, got {w}×{h}")
    if w < 1024:
        warnings.warn(
            f"Source image is {w}×{h}, 1024×1024 recommended for best quality"
        )
    return img


def has_transparency(image: Image.Image) -> bool:
    """Check if image has an alpha channel with any non-opaque pixels."""
    if image.mode != "RGBA":
        return False
    alpha = image.getchannel("A")
    extrema = alpha.getextrema()
    min_alpha: int = extrema[0]  # type: ignore[assignment]
    return min_alpha < 255
