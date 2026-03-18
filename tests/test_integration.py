"""Integration test — run all platforms end-to-end."""

from __future__ import annotations

import pathlib

from iconforge.cli import run
from iconforge.platforms import VALID_PLATFORMS


class TestFullGeneration:
    def test_all_platforms(
        self, square_1024: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        run(
            source=square_1024,
            platforms=VALID_PLATFORMS,
            output_dir=tmp_path,
            options={"android_bg": "#FFFFFF"},
        )
        # Spot-check key outputs
        assert (tmp_path / "ios" / "AppIcon.appiconset" / "Contents.json").exists()
        assert (tmp_path / "android" / "mipmap-xxxhdpi" / "ic_launcher.png").exists()
        assert (tmp_path / "macos" / "AppIcon.icns").exists()
        assert (tmp_path / "windows" / "app.ico").exists()
        assert (tmp_path / "web" / "manifest.json").exists()
        assert (tmp_path / "linux" / "app.desktop").exists()
