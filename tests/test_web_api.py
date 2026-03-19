"""Tests for glyphkit web API endpoints."""

from __future__ import annotations

import json
import pathlib
from io import BytesIO

import pytest
from PIL import Image

from glyphkit.web.app import app, _cleanup_output

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client and clean up after."""
    _cleanup_output()
    with TestClient(app) as c:
        yield c
    _cleanup_output()


@pytest.fixture
def png_bytes() -> bytes:
    """Create a valid 1024x1024 PNG as bytes."""
    img = Image.new("RGBA", (1024, 1024), (255, 0, 0, 255))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def transparent_png_bytes() -> bytes:
    """Create a PNG with transparency."""
    img = Image.new("RGBA", (1024, 1024), (255, 0, 0, 128))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def small_png_bytes() -> bytes:
    """Create a 512x512 PNG."""
    img = Image.new("RGBA", (512, 512), (0, 255, 0, 255))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def non_square_png_bytes() -> bytes:
    """Create a non-square PNG."""
    img = Image.new("RGB", (100, 200), (0, 0, 255))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestValidateEndpoint:
    def test_valid_image(self, client: TestClient, png_bytes: bytes) -> None:
        resp = client.post("/api/validate", files={"image": ("icon.png", png_bytes, "image/png")})
        assert resp.status_code == 200
        data = resp.json()
        assert data["width"] == 1024
        assert data["height"] == 1024
        assert data["is_square"] is True
        assert data["has_transparency"] is False
        assert data["warnings"] == []

    def test_transparent_image(self, client: TestClient, transparent_png_bytes: bytes) -> None:
        resp = client.post("/api/validate", files={"image": ("icon.png", transparent_png_bytes, "image/png")})
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_transparency"] is True
        assert any("transparency" in w.lower() for w in data["warnings"])

    def test_small_image_warns(self, client: TestClient, small_png_bytes: bytes) -> None:
        resp = client.post("/api/validate", files={"image": ("icon.png", small_png_bytes, "image/png")})
        assert resp.status_code == 200
        assert any("1024" in w for w in resp.json()["warnings"])

    def test_non_square_rejects(self, client: TestClient, non_square_png_bytes: bytes) -> None:
        resp = client.post("/api/validate", files={"image": ("icon.png", non_square_png_bytes, "image/png")})
        assert resp.status_code == 400
        assert "square" in resp.json()["detail"].lower()

    def test_non_png_rejects(self, client: TestClient) -> None:
        img = Image.new("RGB", (100, 100))
        buf = BytesIO()
        img.save(buf, format="JPEG")
        resp = client.post("/api/validate", files={"image": ("icon.jpg", buf.getvalue(), "image/jpeg")})
        assert resp.status_code == 400


class TestGenerateEndpoint:
    def test_generate_single_platform(self, client: TestClient, png_bytes: bytes) -> None:
        resp = client.post(
            "/api/generate",
            files={"image": ("icon.png", png_bytes, "image/png")},
            data={"platforms": '["linux"]', "android_bg": "#FFFFFF"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "linux" in data["platforms"]
        assert data["platforms"]["linux"]["file_count"] > 0
        assert all("preview_url" in f for f in data["platforms"]["linux"]["files"])

    def test_generate_multiple_platforms(self, client: TestClient, png_bytes: bytes) -> None:
        resp = client.post(
            "/api/generate",
            files={"image": ("icon.png", png_bytes, "image/png")},
            data={"platforms": '["linux", "windows"]', "android_bg": "#FFFFFF"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "linux" in data["platforms"]
        assert "windows" in data["platforms"]

    def test_invalid_platform(self, client: TestClient, png_bytes: bytes) -> None:
        resp = client.post(
            "/api/generate",
            files={"image": ("icon.png", png_bytes, "image/png")},
            data={"platforms": '["bogus"]', "android_bg": "#FFFFFF"},
        )
        assert resp.status_code == 400
        assert "invalid" in resp.json()["detail"].lower()

    def test_bad_platforms_json(self, client: TestClient, png_bytes: bytes) -> None:
        resp = client.post(
            "/api/generate",
            files={"image": ("icon.png", png_bytes, "image/png")},
            data={"platforms": "not json", "android_bg": "#FFFFFF"},
        )
        assert resp.status_code == 422


class TestPreviewEndpoint:
    def test_preview_after_generate(self, client: TestClient, png_bytes: bytes) -> None:
        gen_resp = client.post(
            "/api/generate",
            files={"image": ("icon.png", png_bytes, "image/png")},
            data={"platforms": '["linux"]', "android_bg": "#FFFFFF"},
        )
        files = gen_resp.json()["platforms"]["linux"]["files"]
        png_files = [f for f in files if f["name"].endswith(".png")]
        resp = client.get(png_files[0]["preview_url"])
        assert resp.status_code == 200

    def test_preview_without_generate(self, client: TestClient) -> None:
        resp = client.get("/api/preview/linux/hicolor/32x32/apps/icon.png")
        assert resp.status_code == 404


class TestDownloadEndpoint:
    def test_download_zip(self, client: TestClient, png_bytes: bytes) -> None:
        client.post(
            "/api/generate",
            files={"image": ("icon.png", png_bytes, "image/png")},
            data={"platforms": '["linux"]', "android_bg": "#FFFFFF"},
        )
        resp = client.get("/api/download")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/zip"

    def test_download_without_generate(self, client: TestClient) -> None:
        resp = client.get("/api/download")
        assert resp.status_code == 404


class TestOpenFolderEndpoint:
    def test_open_folder_without_generate(self, client: TestClient) -> None:
        resp = client.post("/api/open-folder")
        assert resp.status_code == 404
