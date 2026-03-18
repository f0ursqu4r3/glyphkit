"""Tests for core image loading and validation."""

from __future__ import annotations

import pathlib
import warnings

import pytest
from PIL import Image

from iconforge.core import (
    IconforgeError,
    has_transparency,
    load_and_validate_image,
    resize_image,
)


class TestLoadAndValidateImage:
    def test_loads_valid_square_png(self, square_1024: pathlib.Path) -> None:
        img = load_and_validate_image(square_1024)
        assert img.size == (1024, 1024)

    def test_rejects_missing_file(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(IconforgeError, match="File not found"):
            load_and_validate_image(tmp_path / "nope.png")

    def test_rejects_non_png(self, tmp_path: pathlib.Path) -> None:
        jpg = tmp_path / "icon.jpg"
        Image.new("RGB", (100, 100)).save(jpg)
        with pytest.raises(IconforgeError, match="Unsupported format"):
            load_and_validate_image(jpg)

    def test_rejects_non_square(self, non_square: pathlib.Path) -> None:
        with pytest.raises(IconforgeError, match="must be square"):
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
