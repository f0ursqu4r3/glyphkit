"""Windows .ico generator."""

from __future__ import annotations

import pathlib

from PIL import Image

from iconforge.core import resize_image

ICO_SIZES: list[int] = [16, 24, 32, 48, 64, 128, 256]


def generate(source: Image.Image, output_dir: pathlib.Path, options: dict) -> list[pathlib.Path]:
    """Generate Windows .ico with multiple embedded sizes."""
    output_dir.mkdir(parents=True, exist_ok=True)

    sizes = [resize_image(source, s) for s in ICO_SIZES]
    ico_path = output_dir / "app.ico"
    sizes[0].save(ico_path, format="ICO", append_images=sizes[1:], sizes=[(s, s) for s in ICO_SIZES])

    return [ico_path]
