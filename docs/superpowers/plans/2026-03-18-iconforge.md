# iconforge Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local CLI tool that generates correctly sized app icons and platform config files for iOS, Android, macOS, Windows, Web/PWA, and Linux from a single source PNG.

**Architecture:** Platform plugin modules with a shared core. Each platform is a separate module implementing `generate(source, output_dir, options) -> list[Path]`. The CLI dispatches to selected platforms in sequence.

**Tech Stack:** Python 3.11+, Pillow, questionary, icnsutil, uv

**Spec:** `docs/superpowers/specs/2026-03-18-iconforge-design.md`

---

## File Map

| File                                  | Responsibility                                                          |
| ------------------------------------- | ----------------------------------------------------------------------- |
| `pyproject.toml`                      | Project metadata, dependencies, `[project.scripts]` entrypoint          |
| `src/iconforge/__init__.py`           | Package init, version                                                   |
| `src/iconforge/core.py`               | `IconforgeError`, `load_and_validate_image()`, `resize_image()`         |
| `src/iconforge/cli.py`                | argparse flags, questionary prompts, dispatch loop                      |
| `src/iconforge/platforms/__init__.py` | `PLATFORM_REGISTRY` dict mapping name → generate fn                     |
| `src/iconforge/platforms/ios.py`      | iOS icon sizes + `Contents.json` generation                             |
| `src/iconforge/platforms/android.py`  | Android mipmap PNGs + adaptive icon XMLs                                |
| `src/iconforge/platforms/macos.py`    | macOS icon sizes + `Contents.json` + `.icns`                            |
| `src/iconforge/platforms/windows.py`  | `.ico` file with embedded sizes                                         |
| `src/iconforge/platforms/web.py`      | PWA icons + `manifest.json` + `browserconfig.xml` + `head-snippet.html` |
| `src/iconforge/platforms/linux.py`    | hicolor PNGs + `.desktop` stub                                          |
| `tests/conftest.py`                   | Shared test fixtures (dummy square images)                              |
| `tests/test_core.py`                  | Tests for validation and resize                                         |
| `tests/test_ios.py`                   | Tests for iOS generator                                                 |
| `tests/test_android.py`               | Tests for Android generator                                             |
| `tests/test_macos.py`                 | Tests for macOS generator                                               |
| `tests/test_windows.py`               | Tests for Windows generator                                             |
| `tests/test_web.py`                   | Tests for Web/PWA generator                                             |
| `tests/test_linux.py`                 | Tests for Linux generator                                               |
| `tests/test_cli.py`                   | Tests for CLI argument parsing and dispatch                             |

---

## Task 1: Project Scaffold + uv Setup

**Files:**

- Create: `pyproject.toml`
- Create: `src/iconforge/__init__.py`
- Create: `src/iconforge/core.py` (empty, just `IconforgeError`)
- Create: `src/iconforge/cli.py` (stub `main()`)
- Create: `src/iconforge/platforms/__init__.py` (empty `PLATFORM_REGISTRY`)

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "iconforge"
version = "0.1.0"
description = "Universal app icon generator"
requires-python = ">=3.11"
dependencies = [
    "Pillow>=10.0",
    "questionary>=2.0",
    "icnsutil>=1.1",
]

[project.scripts]
iconforge = "iconforge.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/iconforge"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[project.optional-dependencies]
dev = ["pytest>=7.0"]
```

- [ ] **Step 2: Create package files**

`src/iconforge/__init__.py`:

```python
"""iconforge — Universal App Icon Generator."""

__version__ = "0.1.0"
```

`src/iconforge/core.py`:

```python
"""Core utilities: image loading, validation, resizing."""

from __future__ import annotations

import pathlib

from PIL import Image


class IconforgeError(Exception):
    """Base exception for iconforge errors."""


def resize_image(source: Image.Image, size: int) -> Image.Image:
    """Resize source image to size×size using LANCZOS resampling."""
    return source.resize((size, size), Image.LANCZOS)


def load_and_validate_image(path: pathlib.Path) -> Image.Image:
    """Load image, validate it is square PNG. Warn if under 1024×1024."""
    if not path.exists():
        raise IconforgeError(f"File not found: {path}")
    if path.suffix.lower() != ".png":
        raise IconforgeError(f"Unsupported format: {path.suffix}. Only PNG is supported.")
    img = Image.open(path)
    w, h = img.size
    if w != h:
        raise IconforgeError(f"Image must be square, got {w}×{h}")
    if w < 1024:
        import warnings
        warnings.warn(f"Source image is {w}×{h}, 1024×1024 recommended for best quality")
    return img
```

`src/iconforge/cli.py`:

```python
"""CLI entrypoint for iconforge."""

from __future__ import annotations


def main() -> None:
    """Main entrypoint — will be expanded in Task 8."""
    print("iconforge — not yet implemented")


if __name__ == "__main__":
    main()
```

`src/iconforge/platforms/__init__.py`:

```python
"""Platform registry for iconforge."""

from __future__ import annotations

PLATFORM_REGISTRY: dict[str, object] = {}
```

- [ ] **Step 3: Initialize uv and install**

Run: `uv sync --dev`
Expected: dependencies installed, `.venv` created

- [ ] **Step 4: Verify entrypoint works**

Run: `uv run iconforge`
Expected: prints "iconforge — not yet implemented"

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/ uv.lock
git commit -m "feat: project scaffold with uv, core stubs, and CLI entrypoint"
```

---

## Task 2: Core Module — Validation + Resize (TDD)

**Files:**

- Modify: `src/iconforge/core.py`
- Create: `tests/conftest.py`
- Create: `tests/test_core.py`

- [ ] **Step 1: Create test fixtures**

`tests/conftest.py`:

```python
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
```

- [ ] **Step 2: Write failing tests**

`tests/test_core.py`:

```python
"""Tests for core image loading and validation."""

from __future__ import annotations

import pathlib
import warnings

import pytest
from PIL import Image

from iconforge.core import IconforgeError, load_and_validate_image, resize_image


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
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `uv run pytest tests/test_core.py -v`
Expected: all 7 tests PASS (implementation already written in Task 1)

- [ ] **Step 4: Commit**

```bash
git add tests/
git commit -m "test: add core validation and resize tests"
```

---

## Task 3: iOS Platform Exporter (TDD)

**Files:**

- Create: `src/iconforge/platforms/ios.py`
- Create: `tests/test_ios.py`
- Modify: `src/iconforge/platforms/__init__.py`

- [ ] **Step 1: Write failing test**

`tests/test_ios.py`:

```python
"""Tests for iOS icon generation."""

from __future__ import annotations

import json
import pathlib

from PIL import Image

from iconforge.platforms.ios import generate, SIZES


class TestIOSGenerate:
    def test_creates_appiconset_directory(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        assert (tmp_path / "AppIcon.appiconset").is_dir()

    def test_creates_contents_json(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        contents = tmp_path / "AppIcon.appiconset" / "Contents.json"
        assert contents.exists()
        data = json.loads(contents.read_text())
        assert "images" in data
        assert data["info"]["version"] == 1
        assert data["info"]["author"] == "iconforge"

    def test_creates_all_icon_pngs(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        files = generate(source_image, tmp_path, {})
        png_files = [f for f in files if f.suffix == ".png"]
        assert len(png_files) == len(SIZES)
        for f in png_files:
            assert f.exists()
            img = Image.open(f)
            assert img.size[0] == img.size[1]  # square

    def test_returns_all_created_files(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        files = generate(source_image, tmp_path, {})
        # PNGs + Contents.json
        assert len(files) == len(SIZES) + 1

    def test_1024_icon_present(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        icon_1024 = tmp_path / "AppIcon.appiconset" / "Icon-1024.png"
        assert icon_1024.exists()
        img = Image.open(icon_1024)
        assert img.size == (1024, 1024)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_ios.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'iconforge.platforms.ios'`

- [ ] **Step 3: Implement iOS exporter**

`src/iconforge/platforms/ios.py`:

```python
"""iOS app icon generator."""

from __future__ import annotations

import json
import pathlib

from PIL import Image

from iconforge.core import resize_image

# (name, pt_size, scale) tuples
SIZES: list[tuple[str, float, int]] = [
    ("Icon-20@1x", 20, 1),
    ("Icon-20@2x", 20, 2),
    ("Icon-20@3x", 20, 3),
    ("Icon-29@1x", 29, 1),
    ("Icon-29@2x", 29, 2),
    ("Icon-29@3x", 29, 3),
    ("Icon-40@1x", 40, 1),
    ("Icon-40@2x", 40, 2),
    ("Icon-40@3x", 40, 3),
    ("Icon-60@2x", 60, 2),
    ("Icon-60@3x", 60, 3),
    ("Icon-76@1x", 76, 1),
    ("Icon-76@2x", 76, 2),
    ("Icon-83.5@2x", 83.5, 2),
    ("Icon-1024", 1024, 1),
]


def generate(source: Image.Image, output_dir: pathlib.Path, options: dict) -> list[pathlib.Path]:
    """Generate iOS app icon set."""
    appiconset = output_dir / "AppIcon.appiconset"
    appiconset.mkdir(parents=True, exist_ok=True)

    created: list[pathlib.Path] = []
    images_entries: list[dict] = []

    for name, pt_size, scale in SIZES:
        px = int(pt_size * scale)
        filename = f"{name}.png"
        filepath = appiconset / filename

        resized = resize_image(source, px)
        resized.save(filepath, "PNG")
        created.append(filepath)

        entry: dict = {
            "filename": filename,
            "idiom": "universal",
            "scale": f"{scale}x",
            "size": f"{pt_size}x{pt_size}" if pt_size == int(pt_size) else f"{pt_size}x{pt_size}",
        }
        images_entries.append(entry)

    contents = {
        "images": images_entries,
        "info": {"author": "iconforge", "version": 1},
    }
    contents_path = appiconset / "Contents.json"
    contents_path.write_text(json.dumps(contents, indent=2) + "\n")
    created.append(contents_path)

    return created
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_ios.py -v`
Expected: all 5 tests PASS

- [ ] **Step 5: Register in platform registry**

Update `src/iconforge/platforms/__init__.py`:

```python
"""Platform registry for iconforge."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pathlib
    from PIL import Image

    PlatformGenerator = type[
        tuple[Image.Image, pathlib.Path, dict], list[pathlib.Path]
    ]

from iconforge.platforms.ios import generate as ios_generate

PLATFORM_REGISTRY: dict[str, object] = {
    "ios": ios_generate,
}
```

- [ ] **Step 6: Commit**

```bash
git add src/iconforge/platforms/ tests/test_ios.py
git commit -m "feat: iOS icon generator with Contents.json"
```

---

## Task 4: Android Platform Exporter (TDD)

**Files:**

- Create: `src/iconforge/platforms/android.py`
- Create: `tests/test_android.py`
- Modify: `src/iconforge/platforms/__init__.py`

- [ ] **Step 1: Write failing test**

`tests/test_android.py`:

```python
"""Tests for Android icon generation."""

from __future__ import annotations

import pathlib

from PIL import Image

from iconforge.platforms.android import generate, DENSITIES


class TestAndroidGenerate:
    def test_creates_mipmap_directories(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        for density, _size in DENSITIES:
            assert (tmp_path / f"mipmap-{density}" / "ic_launcher.png").exists()

    def test_correct_sizes_per_density(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        for density, size in DENSITIES:
            img = Image.open(tmp_path / f"mipmap-{density}" / "ic_launcher.png")
            assert img.size == (size, size)

    def test_creates_adaptive_icon_xml(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        ic_launcher = tmp_path / "res" / "mipmap-anydpi-v26" / "ic_launcher.xml"
        ic_round = tmp_path / "res" / "mipmap-anydpi-v26" / "ic_launcher_round.xml"
        assert ic_launcher.exists()
        assert ic_round.exists()
        content = ic_launcher.read_text()
        assert "adaptive-icon" in content

    def test_creates_background_drawable(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        bg = tmp_path / "res" / "drawable" / "ic_launcher_background.xml"
        assert bg.exists()
        assert "#FFFFFF" in bg.read_text()

    def test_creates_foreground_pngs(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        for density, size in DENSITIES:
            fg = tmp_path / f"mipmap-{density}" / "ic_launcher_foreground.png"
            assert fg.exists()
            img = Image.open(fg)
            # Adaptive icon canvas is 108/48 * size
            canvas = int(size * 108 / 48)
            assert img.size == (canvas, canvas)

    def test_custom_background_color(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {"android_bg": "#FF0000"})
        bg = tmp_path / "res" / "drawable" / "ic_launcher_background.xml"
        assert "#FF0000" in bg.read_text()

    def test_returns_all_files(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        files = generate(source_image, tmp_path, {})
        assert len(files) > 0
        for f in files:
            assert f.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_android.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement Android exporter**

`src/iconforge/platforms/android.py`:

```python
"""Android app icon generator with adaptive icon support."""

from __future__ import annotations

import pathlib

from PIL import Image

from iconforge.core import resize_image

# (density_name, icon_size_px)
DENSITIES: list[tuple[str, int]] = [
    ("mdpi", 48),
    ("hdpi", 72),
    ("xhdpi", 96),
    ("xxhdpi", 144),
    ("xxxhdpi", 192),
]

_ADAPTIVE_ICON_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_background" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
</adaptive-icon>
"""

_BACKGROUND_COLOR_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">{color}</color>
</resources>
"""


def _create_foreground(source: Image.Image, canvas_size: int) -> Image.Image:
    """Place source in the 66/108 safe zone of an adaptive icon canvas."""
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    safe_zone = int(canvas_size * 66 / 108)
    resized = resize_image(source, safe_zone)
    offset = (canvas_size - safe_zone) // 2
    canvas.paste(resized, (offset, offset))
    return canvas


def generate(source: Image.Image, output_dir: pathlib.Path, options: dict) -> list[pathlib.Path]:
    """Generate Android launcher icons with adaptive icon support."""
    created: list[pathlib.Path] = []
    bg_color = options.get("android_bg", "#FFFFFF")

    # Standard mipmap icons
    for density, size in DENSITIES:
        mipmap_dir = output_dir / f"mipmap-{density}"
        mipmap_dir.mkdir(parents=True, exist_ok=True)

        icon_path = mipmap_dir / "ic_launcher.png"
        resized = resize_image(source, size)
        resized.save(icon_path, "PNG")
        created.append(icon_path)

        # Adaptive foreground (108dp canvas at this density)
        canvas_size = int(size * 108 / 48)
        fg = _create_foreground(source, canvas_size)
        fg_path = mipmap_dir / "ic_launcher_foreground.png"
        fg.save(fg_path, "PNG")
        created.append(fg_path)

    # Adaptive icon XML
    anydpi_dir = output_dir / "res" / "mipmap-anydpi-v26"
    anydpi_dir.mkdir(parents=True, exist_ok=True)

    ic_launcher_xml = anydpi_dir / "ic_launcher.xml"
    ic_launcher_xml.write_text(_ADAPTIVE_ICON_XML)
    created.append(ic_launcher_xml)

    ic_round_xml = anydpi_dir / "ic_launcher_round.xml"
    ic_round_xml.write_text(_ADAPTIVE_ICON_XML)
    created.append(ic_round_xml)

    # Background drawable
    drawable_dir = output_dir / "res" / "drawable"
    drawable_dir.mkdir(parents=True, exist_ok=True)

    bg_xml_path = drawable_dir / "ic_launcher_background.xml"
    bg_xml_path.write_text(_BACKGROUND_COLOR_XML.format(color=bg_color))
    created.append(bg_xml_path)

    return created
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_android.py -v`
Expected: all 7 tests PASS

- [ ] **Step 5: Register in platform registry**

Add to `src/iconforge/platforms/__init__.py`:

```python
from iconforge.platforms.android import generate as android_generate

# Add to PLATFORM_REGISTRY:
"android": android_generate,
```

- [ ] **Step 6: Commit**

```bash
git add src/iconforge/platforms/ tests/test_android.py
git commit -m "feat: Android icon generator with adaptive icon support"
```

---

## Task 5: macOS Platform Exporter (TDD)

**Files:**

- Create: `src/iconforge/platforms/macos.py`
- Create: `tests/test_macos.py`
- Modify: `src/iconforge/platforms/__init__.py`

- [ ] **Step 1: Write failing test**

`tests/test_macos.py`:

```python
"""Tests for macOS icon generation."""

from __future__ import annotations

import json
import pathlib

from PIL import Image

from iconforge.platforms.macos import generate, SIZES


class TestMacOSGenerate:
    def test_creates_appiconset(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        assert (tmp_path / "AppIcon.appiconset").is_dir()

    def test_creates_contents_json(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        contents = tmp_path / "AppIcon.appiconset" / "Contents.json"
        data = json.loads(contents.read_text())
        assert "images" in data
        assert data["info"]["author"] == "iconforge"

    def test_creates_all_pngs(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        files = generate(source_image, tmp_path, {})
        png_files = [f for f in files if f.suffix == ".png"]
        assert len(png_files) == len(SIZES)

    def test_creates_icns_file(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        files = generate(source_image, tmp_path, {})
        icns_files = [f for f in files if f.suffix == ".icns"]
        assert len(icns_files) == 1
        assert icns_files[0].exists()

    def test_icon_sizes_correct(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        # Check 512@2x = 1024px
        icon = tmp_path / "AppIcon.appiconset" / "icon_512x512@2x.png"
        assert icon.exists()
        img = Image.open(icon)
        assert img.size == (1024, 1024)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_macos.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement macOS exporter**

`src/iconforge/platforms/macos.py`:

```python
"""macOS app icon generator."""

from __future__ import annotations

import json
import pathlib

import icnsutil
from PIL import Image

from iconforge.core import resize_image

# (filename, base_size, scale)
SIZES: list[tuple[str, int, int]] = [
    ("icon_16x16", 16, 1),
    ("icon_16x16@2x", 16, 2),
    ("icon_32x32", 32, 1),
    ("icon_32x32@2x", 32, 2),
    ("icon_128x128", 128, 1),
    ("icon_128x128@2x", 128, 2),
    ("icon_256x256", 256, 1),
    ("icon_256x256@2x", 256, 2),
    ("icon_512x512", 512, 1),
    ("icon_512x512@2x", 512, 2),
]


def generate(source: Image.Image, output_dir: pathlib.Path, options: dict) -> list[pathlib.Path]:
    """Generate macOS app icon set and .icns file."""
    appiconset = output_dir / "AppIcon.appiconset"
    appiconset.mkdir(parents=True, exist_ok=True)

    created: list[pathlib.Path] = []
    images_entries: list[dict] = []

    for name, base_size, scale in SIZES:
        px = base_size * scale
        filename = f"{name}.png"
        filepath = appiconset / filename

        resized = resize_image(source, px)
        resized.save(filepath, "PNG")
        created.append(filepath)

        images_entries.append({
            "filename": filename,
            "idiom": "mac",
            "scale": f"{scale}x",
            "size": f"{base_size}x{base_size}",
        })

    contents = {
        "images": images_entries,
        "info": {"author": "iconforge", "version": 1},
    }
    contents_path = appiconset / "Contents.json"
    contents_path.write_text(json.dumps(contents, indent=2) + "\n")
    created.append(contents_path)

    # Generate .icns
    icns = icnsutil.IcnsFile()
    for name, base_size, scale in SIZES:
        filepath = appiconset / f"{name}.png"
        icns.add_media(file_path=str(filepath))
    icns_path = output_dir / "AppIcon.icns"
    icns.write(str(icns_path))
    created.append(icns_path)

    return created
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_macos.py -v`
Expected: all 5 tests PASS

- [ ] **Step 5: Register in platform registry**

Add `"macos": macos_generate` to `PLATFORM_REGISTRY`.

- [ ] **Step 6: Commit**

```bash
git add src/iconforge/platforms/ tests/test_macos.py
git commit -m "feat: macOS icon generator with Contents.json and .icns"
```

---

## Task 6: Windows Platform Exporter (TDD)

**Files:**

- Create: `src/iconforge/platforms/windows.py`
- Create: `tests/test_windows.py`
- Modify: `src/iconforge/platforms/__init__.py`

- [ ] **Step 1: Write failing test**

`tests/test_windows.py`:

```python
"""Tests for Windows icon generation."""

from __future__ import annotations

import pathlib

from PIL import Image

from iconforge.platforms.windows import generate, ICO_SIZES


class TestWindowsGenerate:
    def test_creates_ico_file(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        files = generate(source_image, tmp_path, {})
        ico = tmp_path / "app.ico"
        assert ico.exists()
        assert ico in files

    def test_ico_is_valid(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        ico = Image.open(tmp_path / "app.ico")
        assert ico.format == "ICO"

    def test_returns_single_file(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        files = generate(source_image, tmp_path, {})
        assert len(files) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_windows.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement Windows exporter**

`src/iconforge/platforms/windows.py`:

```python
"""Windows .ico generator."""

from __future__ import annotations

import pathlib

from PIL import Image

from iconforge.core import resize_image

ICO_SIZES: list[int] = [16, 24, 32, 48, 64, 128, 256]


def generate(source: Image.Image, output_dir: pathlib.Path, options: dict) -> list[pathlib.Path]:
    """Generate Windows .ico with multiple embedded sizes."""
    output_dir.mkdir(parents=True, exist_ok=True)

    sizes = [resize_image(source, s) for s in ICO_SIZES]
    ico_path = output_dir / "app.ico"
    sizes[0].save(ico_path, format="ICO", append_images=sizes[1:], sizes=[(s, s) for s in ICO_SIZES])

    return [ico_path]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_windows.py -v`
Expected: all 3 tests PASS

- [ ] **Step 5: Register in platform registry**

Add `"windows": windows_generate` to `PLATFORM_REGISTRY`.

- [ ] **Step 6: Commit**

```bash
git add src/iconforge/platforms/ tests/test_windows.py
git commit -m "feat: Windows .ico generator"
```

---

## Task 7: Web/PWA Platform Exporter (TDD)

**Files:**

- Create: `src/iconforge/platforms/web.py`
- Create: `tests/test_web.py`
- Modify: `src/iconforge/platforms/__init__.py`

- [ ] **Step 1: Write failing test**

`tests/test_web.py`:

```python
"""Tests for Web/PWA icon generation."""

from __future__ import annotations

import json
import pathlib

from PIL import Image

from iconforge.platforms.web import generate


class TestWebGenerate:
    def test_creates_favicon_ico(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        assert (tmp_path / "favicon.ico").exists()

    def test_creates_png_icons(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        assert (tmp_path / "icon-192.png").exists()
        assert (tmp_path / "icon-512.png").exists()
        assert (tmp_path / "apple-touch-icon.png").exists()
        img = Image.open(tmp_path / "apple-touch-icon.png")
        assert img.size == (180, 180)

    def test_creates_manifest_json(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        manifest = json.loads((tmp_path / "manifest.json").read_text())
        assert "icons" in manifest
        sizes = [i["sizes"] for i in manifest["icons"]]
        assert "192x192" in sizes
        assert "512x512" in sizes

    def test_creates_browserconfig_xml(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        content = (tmp_path / "browserconfig.xml").read_text()
        assert "msapplication" in content.lower() or "square150x150" in content.lower()

    def test_creates_head_snippet(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        generate(source_image, tmp_path, {})
        content = (tmp_path / "head-snippet.html").read_text()
        assert "<link" in content
        assert "apple-touch-icon" in content

    def test_returns_all_files(self, source_image: Image.Image, tmp_path: pathlib.Path) -> None:
        files = generate(source_image, tmp_path, {})
        assert len(files) == 7  # favicon.ico, 3 PNGs, manifest, browserconfig, head-snippet
        for f in files:
            assert f.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_web.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement Web/PWA exporter**

`src/iconforge/platforms/web.py`:

```python
"""Web/PWA icon generator."""

from __future__ import annotations

import json
import pathlib

from PIL import Image

from iconforge.core import resize_image

_PNG_SIZES: dict[str, int] = {
    "icon-192.png": 192,
    "icon-512.png": 512,
    "apple-touch-icon.png": 180,
}

_TILE_SIZES: list[int] = [70, 150, 310]

_HEAD_SNIPPET = """\
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="/icon-192.png" sizes="192x192">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.json">
<meta name="msapplication-config" content="/browserconfig.xml">
"""

_BROWSERCONFIG_TEMPLATE = """\
<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
  <msapplication>
    <tile>
      <square70x70logo src="/icon-70.png"/>
      <square150x150logo src="/icon-150.png"/>
      <square310x310logo src="/icon-310.png"/>
    </tile>
  </msapplication>
</browserconfig>
"""


def generate(source: Image.Image, output_dir: pathlib.Path, options: dict) -> list[pathlib.Path]:
    """Generate Web/PWA icons and config files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    created: list[pathlib.Path] = []

    # favicon.ico (16 + 32)
    ico_16 = resize_image(source, 16)
    ico_32 = resize_image(source, 32)
    favicon_path = output_dir / "favicon.ico"
    ico_16.save(favicon_path, format="ICO", append_images=[ico_32], sizes=[(16, 16), (32, 32)])
    created.append(favicon_path)

    # PNG icons
    for filename, size in _PNG_SIZES.items():
        path = output_dir / filename
        resize_image(source, size).save(path, "PNG")
        created.append(path)

    # manifest.json
    manifest = {
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
        ]
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    created.append(manifest_path)

    # browserconfig.xml
    browserconfig_path = output_dir / "browserconfig.xml"
    browserconfig_path.write_text(_BROWSERCONFIG_TEMPLATE)
    created.append(browserconfig_path)

    # head-snippet.html
    snippet_path = output_dir / "head-snippet.html"
    snippet_path.write_text(_HEAD_SNIPPET)
    created.append(snippet_path)

    return created
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_web.py -v`
Expected: all 6 tests PASS

- [ ] **Step 5: Register in platform registry**

Add `"web": web_generate` to `PLATFORM_REGISTRY`.

- [ ] **Step 6: Commit**

```bash
git add src/iconforge/platforms/ tests/test_web.py
git commit -m "feat: Web/PWA icon generator with manifest, browserconfig, head snippet"
```

---

## Task 8: Linux Platform Exporter (TDD)

**Files:**

- Create: `src/iconforge/platforms/linux.py`
- Create: `tests/test_linux.py`
- Modify: `src/iconforge/platforms/__init__.py`

- [ ] **Step 1: Write failing test**

`tests/test_linux.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_linux.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement Linux exporter**

`src/iconforge/platforms/linux.py`:

```python
"""Linux hicolor icon generator."""

from __future__ import annotations

import pathlib

from PIL import Image

from iconforge.core import resize_image

HICOLOR_SIZES: list[int] = [16, 24, 32, 48, 64, 128, 256, 512]

_DESKTOP_TEMPLATE = """\
[Desktop Entry]
Type=Application
Name=Application
Icon=icon
Exec=application
"""


def generate(source: Image.Image, output_dir: pathlib.Path, options: dict) -> list[pathlib.Path]:
    """Generate Linux hicolor icons and .desktop stub."""
    created: list[pathlib.Path] = []

    for size in HICOLOR_SIZES:
        icon_dir = output_dir / "hicolor" / f"{size}x{size}" / "apps"
        icon_dir.mkdir(parents=True, exist_ok=True)
        icon_path = icon_dir / "icon.png"
        resize_image(source, size).save(icon_path, "PNG")
        created.append(icon_path)

    desktop_path = output_dir / "app.desktop"
    desktop_path.write_text(_DESKTOP_TEMPLATE)
    created.append(desktop_path)

    return created
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_linux.py -v`
Expected: all 3 tests PASS

- [ ] **Step 5: Register in platform registry**

Add `"linux": linux_generate` to `PLATFORM_REGISTRY`.

- [ ] **Step 6: Commit**

```bash
git add src/iconforge/platforms/ tests/test_linux.py
git commit -m "feat: Linux hicolor icon generator with .desktop stub"
```

---

## Task 9: CLI — Argument Parsing + Dispatch (TDD)

**Files:**

- Modify: `src/iconforge/cli.py`
- Create: `tests/test_cli.py`
- Modify: `src/iconforge/platforms/__init__.py` (finalize registry)

- [ ] **Step 1: Finalize platform registry**

`src/iconforge/platforms/__init__.py`:

```python
"""Platform registry for iconforge."""

from __future__ import annotations

import pathlib
from typing import Callable

from PIL import Image

PlatformGenerator = Callable[[Image.Image, pathlib.Path, dict], list[pathlib.Path]]

from iconforge.platforms.ios import generate as ios_generate
from iconforge.platforms.android import generate as android_generate
from iconforge.platforms.macos import generate as macos_generate
from iconforge.platforms.windows import generate as windows_generate
from iconforge.platforms.web import generate as web_generate
from iconforge.platforms.linux import generate as linux_generate

PLATFORM_REGISTRY: dict[str, PlatformGenerator] = {
    "ios": ios_generate,
    "android": android_generate,
    "macos": macos_generate,
    "windows": windows_generate,
    "web": web_generate,
    "linux": linux_generate,
}

VALID_PLATFORMS = list(PLATFORM_REGISTRY.keys())
```

- [ ] **Step 2: Write failing CLI tests**

`tests/test_cli.py`:

```python
"""Tests for CLI argument parsing and dispatch."""

from __future__ import annotations

import pathlib

from iconforge.cli import parse_args, run


class TestParseArgs:
    def test_source_and_platforms_required_in_no_prompt(self) -> None:
        args = parse_args(["--source", "icon.png", "--platforms", "ios,web", "--no-prompt"])
        assert args.source == "icon.png"
        assert args.platforms == "ios,web"
        assert args.no_prompt is True

    def test_default_output_dir(self) -> None:
        args = parse_args(["--source", "icon.png", "--platforms", "ios", "--no-prompt"])
        assert args.output_dir == "./iconforge-output"

    def test_custom_output_dir(self) -> None:
        args = parse_args(["--source", "x.png", "--platforms", "ios", "--output-dir", "/tmp/out", "--no-prompt"])
        assert args.output_dir == "/tmp/out"

    def test_android_bg_default(self) -> None:
        args = parse_args(["--source", "x.png", "--platforms", "android", "--no-prompt"])
        assert args.android_bg == "#FFFFFF"


class TestRun:
    def test_invalid_platform_raises(self, square_1024: pathlib.Path, tmp_path: pathlib.Path) -> None:
        import pytest
        with pytest.raises(SystemExit):
            run(source=square_1024, platforms=["bogus"], output_dir=tmp_path, options={})

    def test_generates_for_single_platform(self, square_1024: pathlib.Path, tmp_path: pathlib.Path) -> None:
        run(source=square_1024, platforms=["linux"], output_dir=tmp_path, options={})
        assert (tmp_path / "linux" / "hicolor" / "32x32" / "apps" / "icon.png").exists()

    def test_generates_for_multiple_platforms(self, square_1024: pathlib.Path, tmp_path: pathlib.Path) -> None:
        run(source=square_1024, platforms=["linux", "windows"], output_dir=tmp_path, options={})
        assert (tmp_path / "linux" / "app.desktop").exists()
        assert (tmp_path / "windows" / "app.ico").exists()
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL — `ImportError: cannot import name 'parse_args'`

- [ ] **Step 4: Implement CLI**

`src/iconforge/cli.py`:

```python
"""CLI entrypoint for iconforge."""

from __future__ import annotations

import argparse
import pathlib
import sys

from iconforge.core import IconforgeError, load_and_validate_image
from iconforge.platforms import PLATFORM_REGISTRY, VALID_PLATFORMS


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="iconforge",
        description="Universal app icon generator",
    )
    parser.add_argument("--source", help="Path to source PNG image")
    parser.add_argument("--platforms", help="Comma-separated platforms: " + ", ".join(VALID_PLATFORMS))
    parser.add_argument("--output-dir", default="./iconforge-output", help="Output directory")
    parser.add_argument("--android-bg", default="#FFFFFF", help="Android adaptive icon background color")
    parser.add_argument("--no-prompt", action="store_true", help="Skip interactive prompts")
    return parser.parse_args(argv)


def run(
    source: pathlib.Path,
    platforms: list[str],
    output_dir: pathlib.Path,
    options: dict,
) -> None:
    """Validate inputs and dispatch to platform generators."""
    # Validate platforms
    invalid = [p for p in platforms if p not in PLATFORM_REGISTRY]
    if invalid:
        print(f"Error: invalid platform(s): {', '.join(invalid)}", file=sys.stderr)
        print(f"Valid platforms: {', '.join(VALID_PLATFORMS)}", file=sys.stderr)
        sys.exit(1)

    img = load_and_validate_image(source)

    for platform_name in platforms:
        print(f"Generating {platform_name} icons...")
        platform_dir = output_dir / platform_name
        generator = PLATFORM_REGISTRY[platform_name]
        files = generator(img, platform_dir, options)
        print(f"  {platform_name}: {len(files)} files created")


def _interactive_prompts() -> tuple[pathlib.Path, list[str], dict]:
    """Run interactive questionary prompts."""
    import questionary

    platforms = questionary.checkbox(
        "Select target platforms:",
        choices=VALID_PLATFORMS,
    ).ask()
    if not platforms:
        print("No platforms selected.")
        sys.exit(0)

    source_str = questionary.path("Source image path:").ask()
    if not source_str:
        print("No source image provided.")
        sys.exit(1)

    options: dict = {}
    if "android" in platforms:
        bg = questionary.text(
            "Android background color (hex):",
            default="#FFFFFF",
        ).ask()
        options["android_bg"] = bg or "#FFFFFF"

    return pathlib.Path(source_str), platforms, options


def main() -> None:
    """Main entrypoint."""
    args = parse_args()

    if args.no_prompt:
        if not args.source or not args.platforms:
            print("Error: --source and --platforms required with --no-prompt", file=sys.stderr)
            sys.exit(1)
        source = pathlib.Path(args.source)
        platforms = [p.strip() for p in args.platforms.split(",")]
        options = {"android_bg": args.android_bg}
    else:
        source, platforms, options = _interactive_prompts()

    output_dir = pathlib.Path(args.output_dir)
    run(source=source, platforms=platforms, output_dir=output_dir, options=options)
    print("Done!")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli.py -v`
Expected: all 7 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/iconforge/cli.py src/iconforge/platforms/__init__.py tests/test_cli.py
git commit -m "feat: CLI with argparse, validation, interactive prompts, and dispatch"
```

---

## Task 10: Integration Test + Full Suite

**Files:**

- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

`tests/test_integration.py`:

```python
"""Integration test — run all platforms end-to-end."""

from __future__ import annotations

import pathlib

from iconforge.cli import run
from iconforge.platforms import VALID_PLATFORMS


class TestFullGeneration:
    def test_all_platforms(self, square_1024: pathlib.Path, tmp_path: pathlib.Path) -> None:
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
```

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest -v`
Expected: all tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration test for all platforms"
```

---

## Task 11: README

**Files:**

- Create: `README.md`

- [ ] **Step 1: Write README**

`README.md`:

````markdown
# iconforge

Universal app icon generator. Takes one source PNG and outputs correctly sized icons + platform config files for iOS, Android, macOS, Windows, Web/PWA, and Linux.

## Install

```bash
uv pip install -e .
```

## Usage

### Interactive

```bash
iconforge
```

Prompts you to select platforms and source image.

### Scripted

```bash
iconforge --source icon.png --platforms ios,android,web --no-prompt
```

### All flags

| Flag           | Default              | Description                                               |
| -------------- | -------------------- | --------------------------------------------------------- |
| `--source`     | —                    | Path to source PNG (1024×1024 recommended)                |
| `--platforms`  | —                    | Comma-separated: ios, android, macos, windows, web, linux |
| `--output-dir` | `./iconforge-output` | Output directory                                          |
| `--android-bg` | `#FFFFFF`            | Android adaptive icon background color                    |
| `--no-prompt`  | false                | Skip interactive prompts (for CI)                         |

## Output

```
iconforge-output/
  ios/          → AppIcon.appiconset with Contents.json
  android/      → mipmap PNGs + adaptive icon XMLs
  macos/        → AppIcon.appiconset + AppIcon.icns
  windows/      → app.ico (multi-size)
  web/          → favicon.ico, PWA icons, manifest.json, browserconfig.xml
  linux/        → hicolor PNGs + app.desktop
```

## Development

```bash
uv sync --dev
uv run pytest -v
```
````

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with usage examples"
```
