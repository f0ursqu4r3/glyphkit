"""Android app icon generator with adaptive icon support."""

from __future__ import annotations

import pathlib

from PIL import Image

from iconforge.core import resize_image

# (density_name, icon_size_px)
DENSITIES: list[tuple[str, int]] = [
    ("mdpi", 48),
    ("hdpi", 72),
    ("xhdpi", 96),
    ("xxhdpi", 144),
    ("xxxhdpi", 192),
]

_ADAPTIVE_ICON_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_background" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
</adaptive-icon>
"""

_BACKGROUND_COLOR_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">{color}</color>
</resources>
"""


def _create_foreground(source: Image.Image, canvas_size: int) -> Image.Image:
    """Place source in the 66/108 safe zone of an adaptive icon canvas."""
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    safe_zone = int(canvas_size * 66 / 108)
    resized = resize_image(source, safe_zone)
    offset = (canvas_size - safe_zone) // 2
    canvas.paste(resized, (offset, offset))
    return canvas


def generate(source: Image.Image, output_dir: pathlib.Path, options: dict) -> list[pathlib.Path]:
    """Generate Android launcher icons with adaptive icon support."""
    created: list[pathlib.Path] = []
    bg_color = options.get("android_bg", "#FFFFFF")

    # Standard mipmap icons
    for density, size in DENSITIES:
        mipmap_dir = output_dir / f"mipmap-{density}"
        mipmap_dir.mkdir(parents=True, exist_ok=True)

        icon_path = mipmap_dir / "ic_launcher.png"
        resized = resize_image(source, size)
        resized.save(icon_path, "PNG")
        created.append(icon_path)

        # Adaptive foreground (108dp canvas at this density)
        canvas_size = int(size * 108 / 48)
        fg = _create_foreground(source, canvas_size)
        fg_path = mipmap_dir / "ic_launcher_foreground.png"
        fg.save(fg_path, "PNG")
        created.append(fg_path)

    # Adaptive icon XML
    anydpi_dir = output_dir / "res" / "mipmap-anydpi-v26"
    anydpi_dir.mkdir(parents=True, exist_ok=True)

    ic_launcher_xml = anydpi_dir / "ic_launcher.xml"
    ic_launcher_xml.write_text(_ADAPTIVE_ICON_XML)
    created.append(ic_launcher_xml)

    ic_round_xml = anydpi_dir / "ic_launcher_round.xml"
    ic_round_xml.write_text(_ADAPTIVE_ICON_XML)
    created.append(ic_round_xml)

    # Background drawable
    drawable_dir = output_dir / "res" / "drawable"
    drawable_dir.mkdir(parents=True, exist_ok=True)

    bg_xml_path = drawable_dir / "ic_launcher_background.xml"
    bg_xml_path.write_text(_BACKGROUND_COLOR_XML.format(color=bg_color))
    created.append(bg_xml_path)

    return created
