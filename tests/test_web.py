"""Tests for Web/PWA icon generation."""

from __future__ import annotations

import json
import pathlib

from PIL import Image

from glyphkit.platforms.web import generate


class TestWebGenerate:
    def test_creates_favicon_ico(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        generate(source_image, tmp_path, {})
        assert (tmp_path / "favicon.ico").exists()

    def test_creates_png_icons(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        generate(source_image, tmp_path, {})
        assert (tmp_path / "icon-192.png").exists()
        assert (tmp_path / "icon-512.png").exists()
        assert (tmp_path / "apple-touch-icon.png").exists()
        img = Image.open(tmp_path / "apple-touch-icon.png")
        assert img.size == (180, 180)

    def test_creates_tile_pngs(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        generate(source_image, tmp_path, {})
        for size in [70, 150, 310]:
            tile = tmp_path / f"icon-{size}.png"
            assert tile.exists()
            img = Image.open(tile)
            assert img.size == (size, size)

    def test_creates_manifest_json(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        generate(source_image, tmp_path, {})
        manifest = json.loads((tmp_path / "manifest.json").read_text())
        assert "icons" in manifest
        sizes = [i["sizes"] for i in manifest["icons"]]
        assert "192x192" in sizes
        assert "512x512" in sizes

    def test_creates_browserconfig_xml(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        generate(source_image, tmp_path, {})
        content = (tmp_path / "browserconfig.xml").read_text()
        assert "msapplication" in content.lower() or "square150x150" in content.lower()

    def test_creates_head_snippet(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        generate(source_image, tmp_path, {})
        content = (tmp_path / "head-snippet.html").read_text()
        assert "<link" in content
        assert "apple-touch-icon" in content

    def test_returns_all_files(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        files = generate(source_image, tmp_path, {})
        assert (
            len(files) == 10
        )  # favicon.ico, 3 PNGs, 3 tile PNGs, manifest, browserconfig, head-snippet
        for f in files:
            assert f.exists()
