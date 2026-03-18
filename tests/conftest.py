"""Shared test fixtures."""

from __future__ import annotations

import pathlib

import pytest
from PIL import Image


@pytest.fixture
def square_1024(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a 1024×1024 red PNG."""
    img = Image.new("RGBA", (1024, 1024), (255, 0, 0, 255))
    path = tmp_path / "icon.png"
    img.save(path)
    return path


@pytest.fixture
def square_512(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a 512×512 PNG (under recommended size)."""
    img = Image.new("RGBA", (512, 512), (0, 255, 0, 255))
    path = tmp_path / "small_icon.png"
    img.save(path)
    return path


@pytest.fixture
def non_square(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a non-square PNG."""
    img = Image.new("RGB", (100, 200), (0, 0, 255))
    path = tmp_path / "rect.png"
    img.save(path)
    return path


@pytest.fixture
def source_image() -> Image.Image:
    """In-memory 1024×1024 RGBA image for platform tests."""
    return Image.new("RGBA", (1024, 1024), (255, 0, 0, 255))
