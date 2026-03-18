"""Tests for Linux icon generation."""

from __future__ import annotations

import pathlib

from PIL import Image

from iconforge.platforms.linux import generate, HICOLOR_SIZES


class TestLinuxGenerate:
    def test_creates_hicolor_directories(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        for size in HICOLOR_SIZES:
            icon = tmp_path / "hicolor" / f"{size}x{size}" / "apps" / "icon.png"
            assert icon.exists()
            img = Image.open(icon)
            assert img.size == (size, size)

    def test_creates_desktop_file(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        desktop = tmp_path / "app.desktop"
        assert desktop.exists()
        content = desktop.read_text()
        assert "Icon=icon" in content
        assert "[Desktop Entry]" in content

    def test_returns_all_files(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        files = generate(source_image, tmp_path, {})
        # 8 PNGs + 1 .desktop
        assert len(files) == len(HICOLOR_SIZES) + 1
