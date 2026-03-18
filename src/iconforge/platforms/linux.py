"""Linux hicolor icon generator."""

from __future__ import annotations

import pathlib

from PIL import Image

from iconforge.core import resize_image

HICOLOR_SIZES: list[int] = [16, 24, 32, 48, 64, 128, 256, 512]

_DESKTOP_TEMPLATE = """\
[Desktop Entry]
Type=Application
Name=Application
Icon=icon
Exec=application
"""


def generate(source: Image.Image, output_dir: pathlib.Path, options: dict) -> list[pathlib.Path]:
    """Generate Linux hicolor icons and .desktop stub."""
    created: list[pathlib.Path] = []

    for size in HICOLOR_SIZES:
        icon_dir = output_dir / "hicolor" / f"{size}x{size}" / "apps"
        icon_dir.mkdir(parents=True, exist_ok=True)
        icon_path = icon_dir / "icon.png"
        resize_image(source, size).save(icon_path, "PNG")
        created.append(icon_path)

    desktop_path = output_dir / "app.desktop"
    desktop_path.write_text(_DESKTOP_TEMPLATE)
    created.append(desktop_path)

    return created
