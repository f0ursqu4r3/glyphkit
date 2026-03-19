"""Tests for CLI argument parsing and dispatch."""

from __future__ import annotations

import pathlib

from glyphkit.cli import parse_args, run


class TestParseArgs:
    def test_source_and_platforms_required_in_no_prompt(self) -> None:
        args = parse_args(
            ["--source", "icon.png", "--platforms", "ios,web", "--no-prompt"]
        )
        assert args.source == ["icon.png"]
        assert args.platforms == "ios,web"
        assert args.no_prompt is True

    def test_default_output_dir(self) -> None:
        args = parse_args(["--source", "icon.png", "--platforms", "ios", "--no-prompt"])
        assert args.output_dir == "./glyphkit-output"

    def test_custom_output_dir(self) -> None:
        args = parse_args(
            [
                "--source",
                "x.png",
                "--platforms",
                "ios",
                "--output-dir",
                "/tmp/out",
                "--no-prompt",
            ]
        )
        assert args.output_dir == "/tmp/out"

    def test_android_bg_default(self) -> None:
        args = parse_args(
            ["--source", "x.png", "--platforms", "android", "--no-prompt"]
        )
        assert args.android_bg == "#FFFFFF"


class TestRun:
    def test_invalid_platform_raises(
        self, square_1024: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        import pytest
        from glyphkit.core import GlyphkitError

        with pytest.raises(GlyphkitError, match="Invalid platform"):
            run(
                source=square_1024, platforms=["bogus"], output_dir=tmp_path, options={}
            )

    def test_generates_for_single_platform(
        self, square_1024: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        run(source=square_1024, platforms=["linux"], output_dir=tmp_path, options={})
        assert (tmp_path / "linux" / "hicolor" / "32x32" / "apps" / "icon.png").exists()

    def test_generates_for_multiple_platforms(
        self, square_1024: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        run(
            source=square_1024,
            platforms=["linux", "windows"],
            output_dir=tmp_path,
            options={},
        )
        assert (tmp_path / "linux" / "app.desktop").exists()
        assert (tmp_path / "windows" / "app.ico").exists()


class TestBatchMode:
    def test_multiple_sources(self, square_1024: pathlib.Path, tmp_path: pathlib.Path) -> None:
        """Batch mode creates subdirectories per source."""
        # Create a second source
        from PIL import Image
        second = tmp_path / "second.png"
        Image.new("RGBA", (1024, 1024), (0, 0, 255, 255)).save(second)

        # Each source gets output_dir/stem/platform/...
        output = tmp_path / "output"
        run(source=square_1024, platforms=["linux"], output_dir=output / square_1024.stem, options={})
        run(source=second, platforms=["linux"], output_dir=output / "second", options={})

        assert (output / square_1024.stem / "linux" / "app.desktop").exists()
        assert (output / "second" / "linux" / "app.desktop").exists()
