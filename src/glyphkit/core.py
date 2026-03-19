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


SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".webp", ".svg"}


def load_and_validate_image(path: pathlib.Path) -> Image.Image:
    """Load image, validate it is square. Auto-converts JPEG/WebP to RGBA.

    Supported formats: PNG, JPEG, WebP, SVG.
    SVG requires cairosvg — rasterized at 1024×1024 by default.
    """
    if not path.exists():
        raise GlyphkitError(f"File not found: {path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        raise GlyphkitError(
            f"Unsupported format: {suffix}. "
            f"Supported: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )

    if suffix == ".svg":
        img = _load_svg(path)
    else:
        img = Image.open(path)

    # Convert to RGBA for consistent processing
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    w, h = img.size
    if w != h:
        raise GlyphkitError(f"Image must be square, got {w}×{h}")
    if w < 1024:
        warnings.warn(
            f"Source image is {w}×{h}, 1024×1024 recommended for best quality"
        )
    return img


def _load_svg(path: pathlib.Path, size: int = 1024) -> Image.Image:
    """Rasterize SVG to a PIL Image at the given size."""
    try:
        import cairosvg
    except ImportError:
        raise GlyphkitError(
            "SVG support requires cairosvg. Install with: "
            "uv pip install cairosvg"
        )
    from io import BytesIO

    png_data = cairosvg.svg2png(
        url=str(path),
        output_width=size,
        output_height=size,
    )
    return Image.open(BytesIO(png_data))


def has_transparency(image: Image.Image) -> bool:
    """Check if image has an alpha channel with any non-opaque pixels."""
    if image.mode != "RGBA":
        return False
    alpha = image.getchannel("A")
    extrema = alpha.getextrema()
    min_alpha: int = extrema[0]  # type: ignore[assignment]
    return min_alpha < 255


def apply_padding(source: Image.Image, padding_pct: int) -> Image.Image:
    """Add transparent padding around the icon. padding_pct is 0-50."""
    if padding_pct <= 0:
        return source
    w, h = source.size
    pad = int(w * padding_pct / 100)
    new_size = w + pad * 2
    canvas = Image.new("RGBA", (new_size, new_size), (0, 0, 0, 0))
    canvas.paste(source, (pad, pad))
    return canvas


def apply_background(
    source: Image.Image,
    bg_color: str,
    gradient_type: str = "linear",
    gradient_dir: str = "to-br",
) -> Image.Image:
    """Fill transparent areas with a solid color or gradient.

    bg_color: single hex ("#FFFFFF") or two comma-separated hex colors.
    gradient_type: "linear" or "radial" (only used for gradients).
    gradient_dir: "to-right", "to-br", "to-bottom", "to-bl" (linear only).
    """
    if not bg_color:
        return source

    w, h = source.size

    if "," in bg_color:
        color1, color2 = [c.strip() for c in bg_color.split(",", 1)]
        bg = _create_gradient(w, h, color1, color2, gradient_type, gradient_dir)
    else:
        bg = Image.new("RGBA", (w, h), bg_color)

    bg.paste(source, mask=source.split()[3])
    return bg


def _parse_color(hex_color: str) -> tuple[int, int, int]:
    """Parse a hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )


def _create_gradient(
    w: int,
    h: int,
    color1: str,
    color2: str,
    gradient_type: str = "linear",
    gradient_dir: str = "to-br",
) -> Image.Image:
    """Create a gradient using Pillow's built-in interpolation.

    Uses a tiny source image scaled up with LANCZOS for smooth results.
    """
    c1 = _parse_color(color1)
    c2 = _parse_color(color2)

    if gradient_type == "radial":
        return _create_radial_gradient(w, h, c1, c2)

    # Linear gradient via 2x2 corner image
    # Map direction to corner colors
    mid = tuple((a + b) // 2 for a, b in zip(c1, c2))
    corner = Image.new("RGB", (2, 2))

    if gradient_dir == "to-right":
        corner.putpixel((0, 0), c1)
        corner.putpixel((1, 0), c2)
        corner.putpixel((0, 1), c1)
        corner.putpixel((1, 1), c2)
    elif gradient_dir == "to-bottom":
        corner.putpixel((0, 0), c1)
        corner.putpixel((1, 0), c1)
        corner.putpixel((0, 1), c2)
        corner.putpixel((1, 1), c2)
    elif gradient_dir == "to-bl":
        corner.putpixel((0, 0), mid)
        corner.putpixel((1, 0), c1)
        corner.putpixel((0, 1), c2)
        corner.putpixel((1, 1), mid)
    else:  # to-br (default diagonal)
        corner.putpixel((0, 0), c1)
        corner.putpixel((1, 0), mid)
        corner.putpixel((0, 1), mid)
        corner.putpixel((1, 1), c2)

    gradient = corner.resize((w, h), Resampling.LANCZOS)
    return gradient.convert("RGBA")


def _create_radial_gradient(
    w: int, h: int, c1: tuple[int, int, int], c2: tuple[int, int, int]
) -> Image.Image:
    """Create a radial gradient (center = c1, edges = c2)."""
    import math

    # Use a 1D distance map approach — build at small size, scale up
    small = min(w, 64)
    img = Image.new("RGB", (small, small))
    cx, cy = small / 2, small / 2
    max_dist = math.sqrt(cx * cx + cy * cy)

    for y in range(small):
        for x in range(small):
            dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            t = min(dist / max_dist, 1.0)
            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)
            img.putpixel((x, y), (r, g, b))

    gradient = img.resize((w, h), Resampling.LANCZOS)
    return gradient.convert("RGBA")
