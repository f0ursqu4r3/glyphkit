"""Tests for core image loading and validation."""

from __future__ import annotations

import pathlib
import warnings

import pytest
from PIL import Image

from glyphkit.core import (
    GlyphkitError,
    apply_background,
    apply_padding,
    has_transparency,
    load_and_validate_image,
    resize_image,
)


class TestLoadAndValidateImage:
    def test_loads_valid_square_png(self, square_1024: pathlib.Path) -> None:
        img = load_and_validate_image(square_1024)
        assert img.size == (1024, 1024)

    def test_rejects_missing_file(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(GlyphkitError, match="File not found"):
            load_and_validate_image(tmp_path / "nope.png")

    def test_accepts_jpeg(self, tmp_path: pathlib.Path) -> None:
        jpg = tmp_path / "icon.jpg"
        Image.new("RGB", (1024, 1024)).save(jpg)
        img = load_and_validate_image(jpg)
        assert img.mode == "RGBA"
        assert img.size == (1024, 1024)

    def test_accepts_webp(self, tmp_path: pathlib.Path) -> None:
        webp = tmp_path / "icon.webp"
        Image.new("RGB", (1024, 1024)).save(webp, "WEBP")
        img = load_and_validate_image(webp)
        assert img.mode == "RGBA"

    def test_rejects_unsupported_format(self, tmp_path: pathlib.Path) -> None:
        bmp = tmp_path / "icon.bmp"
        Image.new("RGB", (100, 100)).save(bmp)
        with pytest.raises(GlyphkitError, match="Unsupported format"):
            load_and_validate_image(bmp)

    def test_rejects_non_square(self, non_square: pathlib.Path) -> None:
        with pytest.raises(GlyphkitError, match="must be square"):
            load_and_validate_image(non_square)

    def test_warns_under_1024(self, square_512: pathlib.Path) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            img = load_and_validate_image(square_512)
            assert img.size == (512, 512)
            assert len(w) == 1
            assert "1024" in str(w[0].message)


class TestResizeImage:
    def test_resizes_to_target(self, source_image: Image.Image) -> None:
        result = resize_image(source_image, 64)
        assert result.size == (64, 64)

    def test_preserves_rgba(self, source_image: Image.Image) -> None:
        result = resize_image(source_image, 128)
        assert result.mode == "RGBA"


class TestApplyPadding:
    def test_no_padding(self, source_image: Image.Image) -> None:
        result = apply_padding(source_image, 0)
        assert result.size == (1024, 1024)

    def test_ten_percent_padding(self, source_image: Image.Image) -> None:
        result = apply_padding(source_image, 10)
        # 1024 + 2*(1024*0.1) = 1024 + 204.8 ≈ 1228 (int rounding)
        assert result.size[0] > 1024
        assert result.size[0] == result.size[1]


class TestApplyBackground:
    def test_fills_transparent(self) -> None:
        img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        result = apply_background(img, "#FF0000")
        pixel = result.getpixel((50, 50))
        assert pixel[0] == 255  # Red
        assert pixel[3] == 255  # Opaque

    def test_empty_color_noop(self, source_image: Image.Image) -> None:
        result = apply_background(source_image, "")
        assert result is source_image

    def test_gradient_fill(self) -> None:
        img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        result = apply_background(img, "#FF0000,#0000FF")
        assert result.size == (100, 100)
        # Top-left should be reddish, bottom-right should be bluish
        tl = result.getpixel((0, 0))
        br = result.getpixel((99, 99))
        assert tl[0] > tl[2]  # More red than blue at top-left
        assert br[2] > br[0]  # More blue than red at bottom-right

    def test_radial_gradient(self) -> None:
        img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        result = apply_background(img, "#FF0000,#0000FF", gradient_type="radial")
        center = result.getpixel((50, 50))
        edge = result.getpixel((0, 0))
        assert center[0] > edge[0]  # Center more red (c1)

    def test_horizontal_gradient(self) -> None:
        img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        result = apply_background(img, "#FF0000,#0000FF", gradient_dir="to-right")
        left = result.getpixel((0, 50))
        right = result.getpixel((99, 50))
        assert left[0] > right[0]  # Left more red
        assert right[2] > left[2]  # Right more blue


class TestHasTransparency:
    def test_opaque_image(self) -> None:
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        assert has_transparency(img) is False

    def test_transparent_image(self) -> None:
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 128))
        assert has_transparency(img) is True

    def test_rgb_image(self) -> None:
        img = Image.new("RGB", (10, 10), (255, 0, 0))
        assert has_transparency(img) is False
