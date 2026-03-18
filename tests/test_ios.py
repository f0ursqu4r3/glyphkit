"""Tests for iOS icon generation."""

from __future__ import annotations

import json
import pathlib

from PIL import Image

from iconforge.platforms.ios import generate, SIZES


class TestIOSGenerate:
    def test_creates_appiconset_directory(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        assert (tmp_path / "AppIcon.appiconset").is_dir()

    def test_creates_contents_json(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        contents = tmp_path / "AppIcon.appiconset" / "Contents.json"
        assert contents.exists()
        data = json.loads(contents.read_text())
        assert "images" in data
        assert data["info"]["version"] == 1
        assert data["info"]["author"] == "iconforge"

    def test_creates_all_icon_pngs(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        files = generate(source_image, tmp_path, {})
        png_files = [f for f in files if f.suffix == ".png"]
        assert len(png_files) == len(SIZES)
        for f in png_files:
            assert f.exists()
            img = Image.open(f)
            assert img.size[0] == img.size[1]  # square

    def test_returns_all_created_files(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        files = generate(source_image, tmp_path, {})
        # PNGs + Contents.json
        assert len(files) == len(SIZES) + 1

    def test_1024_icon_present(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        icon_1024 = tmp_path / "AppIcon.appiconset" / "Icon-1024.png"
        assert icon_1024.exists()
        img = Image.open(icon_1024)
        assert img.size == (1024, 1024)

    def test_warns_on_transparency(self, tmp_path: pathlib.Path) -> None:
        import warnings
        # Image with semi-transparent pixels
        img = Image.new("RGBA", (1024, 1024), (255, 0, 0, 128))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            generate(img, tmp_path, {})
            assert len(w) == 1
            assert "transparency" in str(w[0].message).lower()
