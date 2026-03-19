"""Web/PWA icon generator."""

from __future__ import annotations

import json
import pathlib

from PIL import Image

from glyphkit.core import resize_image

_PNG_SIZES: dict[str, int] = {
    "icon-192.png": 192,
    "icon-512.png": 512,
    "apple-touch-icon.png": 180,
}

_TILE_SIZES: list[int] = [70, 150, 310]

_HEAD_SNIPPET = """\
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="/icon-192.png" sizes="192x192">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.json">
<meta name="msapplication-config" content="/browserconfig.xml">
"""

_BROWSERCONFIG_TEMPLATE = """\
<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
  <msapplication>
    <tile>
      <square70x70logo src="/icon-70.png"/>
      <square150x150logo src="/icon-150.png"/>
      <square310x310logo src="/icon-310.png"/>
    </tile>
  </msapplication>
</browserconfig>
"""


def generate(
    source: Image.Image, output_dir: pathlib.Path, options: dict
) -> list[pathlib.Path]:
    """Generate Web/PWA icons and config files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    created: list[pathlib.Path] = []

    # favicon.ico (16 + 32)
    ico_16 = resize_image(source, 16)
    ico_32 = resize_image(source, 32)
    favicon_path = output_dir / "favicon.ico"
    ico_16.save(
        favicon_path, format="ICO", append_images=[ico_32], sizes=[(16, 16), (32, 32)]
    )
    created.append(favicon_path)

    # PNG icons
    for filename, size in _PNG_SIZES.items():
        path = output_dir / filename
        resize_image(source, size).save(path, "PNG")
        created.append(path)

    # MS tile PNGs
    for size in _TILE_SIZES:
        path = output_dir / f"icon-{size}.png"
        resize_image(source, size).save(path, "PNG")
        created.append(path)

    # manifest.json
    manifest = {
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
        ]
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    created.append(manifest_path)

    # browserconfig.xml
    browserconfig_path = output_dir / "browserconfig.xml"
    browserconfig_path.write_text(_BROWSERCONFIG_TEMPLATE)
    created.append(browserconfig_path)

    # head-snippet.html
    snippet_path = output_dir / "head-snippet.html"
    snippet_path.write_text(_HEAD_SNIPPET)
    created.append(snippet_path)

    return created
