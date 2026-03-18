"""iOS app icon generator."""

from __future__ import annotations

import json
import pathlib
import warnings

from PIL import Image

from iconforge.core import has_transparency, resize_image

# (name, pt_size, scale) tuples
SIZES: list[tuple[str, float, int]] = [
    ("Icon-20@1x", 20, 1),
    ("Icon-20@2x", 20, 2),
    ("Icon-20@3x", 20, 3),
    ("Icon-29@1x", 29, 1),
    ("Icon-29@2x", 29, 2),
    ("Icon-29@3x", 29, 3),
    ("Icon-40@1x", 40, 1),
    ("Icon-40@2x", 40, 2),
    ("Icon-40@3x", 40, 3),
    ("Icon-60@2x", 60, 2),
    ("Icon-60@3x", 60, 3),
    ("Icon-76@1x", 76, 1),
    ("Icon-76@2x", 76, 2),
    ("Icon-83.5@2x", 83.5, 2),
    ("Icon-1024", 1024, 1),
]


def generate(
    source: Image.Image, output_dir: pathlib.Path, options: dict
) -> list[pathlib.Path]:
    """Generate iOS app icon set."""
    if has_transparency(source):
        warnings.warn(
            "Source image has transparency. iOS does not support transparent app icons."
        )

    appiconset = output_dir / "AppIcon.appiconset"
    appiconset.mkdir(parents=True, exist_ok=True)

    created: list[pathlib.Path] = []
    images_entries: list[dict] = []

    for name, pt_size, scale in SIZES:
        px = int(pt_size * scale)
        filename = f"{name}.png"
        filepath = appiconset / filename

        resized = resize_image(source, px)
        resized.save(filepath, "PNG")
        created.append(filepath)

        entry: dict = {
            "filename": filename,
            "idiom": "universal",
            "scale": f"{scale}x",
            "size": f"{int(pt_size)}x{int(pt_size)}"
            if pt_size == int(pt_size)
            else f"{pt_size}x{pt_size}",
        }
        images_entries.append(entry)

    contents = {
        "images": images_entries,
        "info": {"author": "iconforge", "version": 1},
    }
    contents_path = appiconset / "Contents.json"
    contents_path.write_text(json.dumps(contents, indent=2) + "\n")
    created.append(contents_path)

    return created
