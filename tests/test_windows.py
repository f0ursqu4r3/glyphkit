"""Tests for Windows icon generation."""

from __future__ import annotations

import pathlib

from PIL import Image

from iconforge.platforms.windows import generate, ICO_SIZES


class TestWindowsGenerate:
    def test_creates_ico_file(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        files = generate(source_image, tmp_path, {})
        ico = tmp_path / "app.ico"
        assert ico.exists()
        assert ico in files

    def test_ico_is_valid(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        generate(source_image, tmp_path, {})
        ico = Image.open(tmp_path / "app.ico")
        assert ico.format == "ICO"

    def test_returns_single_file(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        files = generate(source_image, tmp_path, {})
        assert len(files) == 1
