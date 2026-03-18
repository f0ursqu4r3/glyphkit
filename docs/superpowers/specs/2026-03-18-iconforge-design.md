# iconforge — Universal App Icon Generator

## Overview

A local CLI tool that takes one high-quality source image and outputs correctly sized icons + platform config files for every selected target platform. Fully offline, no network calls.

## Architecture

**Approach: Platform plugin modules.** A core module handles CLI, validation, and image loading. Each platform is a separate module implementing a common `generate(source, output_dir, options)` interface. The core iterates over selected platforms and dispatches.

## Project Structure

```
iconforge/
  pyproject.toml
  src/
    iconforge/
      __init__.py
      cli.py          # argparse + questionary interactive prompts
      core.py          # image loading, validation, resize helpers
      platforms/
        __init__.py    # PLATFORM_REGISTRY mapping name → generate fn
        ios.py
        android.py
        macos.py
        windows.py
        web.py
        linux.py
```

## Dependencies

- `Pillow` — image loading, resizing, ICO generation
- `questionary` — interactive multi-select prompts
- `icnsutil` — cross-platform `.icns` file generation (macOS)

## CLI & Entry Flow

### Interactive mode (default)

`iconforge` with no args launches `questionary` prompts:

1. Multi-select checkboxes for platforms (iOS, Android, macOS, Windows, Web/PWA, Linux)
2. File path prompt for source image (with validation)
3. For Android: optional background color/image prompt (defaults to `#FFFFFF`)

### Scripted mode

```
iconforge --source icon.png --platforms ios,android,web --no-prompt
```

Flags:
- `--source` — path to source image (PNG or SVG)
- `--platforms` — comma-separated list of platforms
- `--output-dir` — output directory (default: `./iconforge-output/`)
- `--android-bg` — Android adaptive icon background color hex or image path (default: `#FFFFFF`)
- `--no-prompt` — skip interactive prompts (for CI/scripted use)

### Validation (in `core.py`)

- Confirm file exists, is PNG or SVG
- Open with Pillow, confirm square aspect ratio (error if not square)
- Warn (don't fail) if under 1024×1024
- Per-platform transparency warnings (iOS doesn't support transparency — warn if alpha channel detected)

## Platform Export Specs

### iOS

- Output: `ios/AppIcon.appiconset/`
- Sizes: 20pt @1x/2x/3x, 29pt @1x/2x/3x, 40pt @1x/2x/3x, 60pt @2x/3x, 76pt @1x/2x, 83.5pt @2x, 1024pt @1x
- Config: `Contents.json` (Xcode asset catalog format)
- Filenames: `Icon-20@2x.png`, etc.

### Android

- Output: `android/mipmap-{mdpi,hdpi,xhdpi,xxhdpi,xxxhdpi}/ic_launcher.png`
- Sizes: 48, 72, 96, 144, 192px
- Adaptive icon support:
  - Foreground: source image with padding
  - Background: solid color XML (default `#FFFFFF`) or provided image
  - Config: `ic_launcher.xml`, `ic_launcher_round.xml` in `res/mipmap-anydpi-v26/`
  - Drawable XMLs: `ic_launcher_background.xml`, `ic_launcher_foreground.xml` in `res/drawable/`

### macOS

- Output: `macos/AppIcon.appiconset/`
- Sizes: 16, 32, 128, 256, 512 @1x and @2x
- Config: `Contents.json` (Xcode asset catalog format)
- Also generates `AppIcon.icns` via `icnsutil`

### Windows

- Output: `windows/app.ico`
- Embedded sizes: 16, 24, 32, 48, 64, 128, 256px
- Generated via Pillow's ICO save

### Web/PWA

- Output: `web/`
- Files: `favicon.ico` (16+32), `icon-192.png`, `icon-512.png`, `apple-touch-icon.png` (180px)
- Config: `manifest.json` (with icon entries), `browserconfig.xml` (MS tiles), `head-snippet.html` (ready-to-paste `<link>` and `<meta>` tags)

### Linux

- Output: `linux/hicolor/{size}x{size}/apps/icon.png`
- Sizes: 16, 24, 32, 48, 64, 128, 256, 512
- Config: `app.desktop` file stub with `Icon=icon`

## Shared Resize Logic

`core.py` provides `resize_image(source: Image, size: int) -> Image` using `Image.LANCZOS` resampling. Each platform module calls this with its size list.

## Output Structure

```
iconforge-output/
  ios/
    AppIcon.appiconset/
      Contents.json
      Icon-20@1x.png ... Icon-1024.png
  android/
    mipmap-mdpi/ic_launcher.png
    ...
    mipmap-xxxhdpi/ic_launcher.png
    res/drawable/ic_launcher_background.xml
    res/drawable/ic_launcher_foreground.xml
    res/mipmap-anydpi-v26/ic_launcher.xml
  macos/
    AppIcon.appiconset/
      Contents.json
      icon_16x16.png ... icon_512x512@2x.png
    AppIcon.icns
  windows/
    app.ico
  web/
    favicon.ico
    icon-192.png
    icon-512.png
    apple-touch-icon.png
    manifest.json
    browserconfig.xml
    head-snippet.html
  linux/
    hicolor/
      16x16/apps/icon.png ... 512x512/apps/icon.png
    app.desktop
```

## Stretch Goals (post-core)

- `--watch` mode: re-generate on source file change
- SVG source support (rasterize at target sizes)
- Background color/padding options per platform
- Summary report printed to stdout after generation

## Tooling

- **Dependency management**: `uv` — `pyproject.toml` with `[project.scripts]` entrypoint, `uv pip install -e .` for local dev, `uv run iconforge` for execution

## Decisions Made

- **`.icns` generation**: Using `icnsutil` (pure Python, cross-platform) rather than macOS-only `iconutil`
- **Architecture**: Platform plugin modules with function-based interface, no class hierarchy
- **Interactive prompts**: `questionary` for multi-select and file path input
- **Dependency management**: `uv` (not pip/poetry)
