"""macOS app icon generator."""

from __future__ import annotations

import json
import pathlib

import icnsutil
from PIL import Image

from iconforge.core import resize_image

# (filename, base_size, scale)
SIZES: list[tuple[str, int, int]] = [
    ("icon_16x16", 16, 1),
    ("icon_16x16@2x", 16, 2),
    ("icon_32x32", 32, 1),
    ("icon_32x32@2x", 32, 2),
    ("icon_128x128", 128, 1),
    ("icon_128x128@2x", 128, 2),
    ("icon_256x256", 256, 1),
    ("icon_256x256@2x", 256, 2),
    ("icon_512x512", 512, 1),
    ("icon_512x512@2x", 512, 2),
]


def generate(
    source: Image.Image, output_dir: pathlib.Path, options: dict
) -> list[pathlib.Path]:
    """Generate macOS app icon set and .icns file."""
    appiconset = output_dir / "AppIcon.appiconset"
    appiconset.mkdir(parents=True, exist_ok=True)

    created: list[pathlib.Path] = []
    images_entries: list[dict] = []

    for name, base_size, scale in SIZES:
        px = base_size * scale
        filename = f"{name}.png"
        filepath = appiconset / filename

        resized = resize_image(source, px)
        resized.save(filepath, "PNG")
        created.append(filepath)

        images_entries.append(
            {
                "filename": filename,
                "idiom": "mac",
                "scale": f"{scale}x",
                "size": f"{base_size}x{base_size}",
            }
        )

    contents = {
        "images": images_entries,
        "info": {"author": "iconforge", "version": 1},
    }
    contents_path = appiconset / "Contents.json"
    contents_path.write_text(json.dumps(contents, indent=2) + "\n")
    created.append(contents_path)

    # Generate .icns
    icns = icnsutil.IcnsFile()
    for name, base_size, scale in SIZES:
        filepath = appiconset / f"{name}.png"
        try:
            icns.add_media(file=str(filepath))
        except (KeyError, ValueError):
            pass  # Skip duplicate pixel sizes (e.g., 16@2x and 32@1x both = 32px)

    icns_path = output_dir / "AppIcon.icns"
    icns.write(str(icns_path))
    created.append(icns_path)

    return created
