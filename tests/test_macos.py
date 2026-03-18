"""Tests for macOS icon generation."""

from __future__ import annotations

import json
import pathlib

from PIL import Image

from iconforge.platforms.macos import generate, SIZES


class TestMacOSGenerate:
    def test_creates_appiconset(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        generate(source_image, tmp_path, {})
        assert (tmp_path / "AppIcon.appiconset").is_dir()

    def test_creates_contents_json(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        generate(source_image, tmp_path, {})
        contents = tmp_path / "AppIcon.appiconset" / "Contents.json"
        data = json.loads(contents.read_text())
        assert "images" in data
        assert data["info"]["author"] == "iconforge"

    def test_creates_all_pngs(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        files = generate(source_image, tmp_path, {})
        png_files = [f for f in files if f.suffix == ".png"]
        assert len(png_files) == len(SIZES)

    def test_creates_icns_file(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        files = generate(source_image, tmp_path, {})
        icns_files = [f for f in files if f.suffix == ".icns"]
        assert len(icns_files) == 1
        assert icns_files[0].exists()

    def test_icon_sizes_correct(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        generate(source_image, tmp_path, {})
        # Check 512@2x = 1024px
        icon = tmp_path / "AppIcon.appiconset" / "icon_512x512@2x.png"
        assert icon.exists()
        img = Image.open(icon)
        assert img.size == (1024, 1024)
