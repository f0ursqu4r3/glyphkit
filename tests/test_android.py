"""Tests for Android icon generation."""

from __future__ import annotations

import pathlib

from PIL import Image

from glyphkit.platforms.android import generate, DENSITIES


class TestAndroidGenerate:
    def test_creates_mipmap_directories(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        generate(source_image, tmp_path, {})
        for density, _size in DENSITIES:
            assert (tmp_path / f"mipmap-{density}" / "ic_launcher.png").exists()

    def test_correct_sizes_per_density(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        generate(source_image, tmp_path, {})
        for density, size in DENSITIES:
            img = Image.open(tmp_path / f"mipmap-{density}" / "ic_launcher.png")
            assert img.size == (size, size)

    def test_creates_adaptive_icon_xml(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        generate(source_image, tmp_path, {})
        ic_launcher = tmp_path / "res" / "mipmap-anydpi-v26" / "ic_launcher.xml"
        ic_round = tmp_path / "res" / "mipmap-anydpi-v26" / "ic_launcher_round.xml"
        assert ic_launcher.exists()
        assert ic_round.exists()
        content = ic_launcher.read_text()
        assert "adaptive-icon" in content

    def test_creates_background_drawable(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        generate(source_image, tmp_path, {})
        bg = tmp_path / "res" / "drawable" / "ic_launcher_background.xml"
        assert bg.exists()
        assert "#FFFFFF" in bg.read_text()

    def test_creates_foreground_pngs(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        generate(source_image, tmp_path, {})
        for density, size in DENSITIES:
            fg = tmp_path / f"mipmap-{density}" / "ic_launcher_foreground.png"
            assert fg.exists()
            img = Image.open(fg)
            # Adaptive icon canvas is 108/48 * size
            canvas = int(size * 108 / 48)
            assert img.size == (canvas, canvas)

    def test_custom_background_color(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        generate(source_image, tmp_path, {"android_bg": "#FF0000"})
        bg = tmp_path / "res" / "drawable" / "ic_launcher_background.xml"
        assert "#FF0000" in bg.read_text()

    def test_returns_all_files(
        self, source_image: Image.Image, tmp_path: pathlib.Path
    ) -> None:
        files = generate(source_image, tmp_path, {})
        assert len(files) > 0
        for f in files:
            assert f.exists()
