# glyphkit

Generate correctly sized app icons for every platform from a single source image.

Drop in a PNG, JPEG, WebP, or SVG. Get back production-ready icons for iOS, Android, macOS, Windows, Web/PWA, and Linux — with platform config files included.

## Install

```bash
uv pip install -e .
```

For the web UI:

```bash
uv pip install -e '.[ui]'
```

## Quick start

### Interactive

```bash
glyphkit
```

Walks you through platform selection, source image, and options.

### Scripted

```bash
glyphkit --source icon.png --platforms ios,android,web --no-prompt
```

### Web UI

```bash
glyphkit --ui
```

Opens a local browser UI with drag-and-drop, live preview, and visual controls.

## CLI flags

| Flag                 | Default             | Description                                                  |
| -------------------- | ------------------- | ------------------------------------------------------------ |
| `--source`           | —                   | Source image path(s). Supports globs (`icons/*.png`)         |
| `--platforms`        | —                   | `ios`, `android`, `macos`, `windows`, `web`, `linux`         |
| `--output-dir`       | `./glyphkit-output` | Where to write generated files                               |
| `--padding`          | `0`                 | Transparent padding around icon (0–50%)                      |
| `--bg-color`         | —                   | Background fill: `#FFFFFF` or `#FF0000,#0000FF` for gradient |
| `--bg-gradient-type` | `linear`            | `linear` or `radial`                                         |
| `--bg-gradient-dir`  | `to-br`             | `to-right`, `to-br`, `to-bottom`, `to-bl`                    |
| `--android-bg`       | `#FFFFFF`           | Android adaptive icon background color                       |
| `--watch`            | —                   | Re-generate when source file changes                         |
| `--copy-path`        | —                   | Copy output directory to clipboard                           |
| `--no-prompt`        | —                   | Skip interactive prompts (for CI/scripts)                    |
| `--ui`               | —                   | Launch the web UI                                            |

## Source formats

PNG, JPEG, WebP, and SVG. Images must be square. 1024×1024 or larger recommended.

SVG support requires `cairosvg`:

```bash
uv pip install cairosvg
```

## Platform output

```text
glyphkit-output/
  ios/
    AppIcon.appiconset/
      Contents.json
      Icon-20@1x.png … Icon-1024.png
  android/
    mipmap-mdpi/ … mipmap-xxxhdpi/
      ic_launcher.png
      ic_launcher_foreground.png
    res/
      drawable/ic_launcher_background.xml
      mipmap-anydpi-v26/ic_launcher.xml
  macos/
    AppIcon.appiconset/
      Contents.json
      icon_16x16.png … icon_512x512@2x.png
    AppIcon.icns
  windows/
    app.ico
  web/
    favicon.ico
    icon-192.png, icon-512.png
    apple-touch-icon.png
    manifest.json
    browserconfig.xml
    head-snippet.html
  linux/
    hicolor/16x16/ … 512x512/apps/icon.png
    app.desktop
```

## Config file

Save defaults in `.glyphkit.toml` at your project root:

```toml
platforms = ["ios", "android", "web"]
output_dir = "./icons"
padding = 5
android_bg = "#FFFFFF"
bg_color = ""
```

CLI flags override config values.

## Batch mode

Process multiple images at once:

```bash
glyphkit --source icons/*.png --platforms ios,web --no-prompt
```

Each source gets its own subdirectory in the output.

## Watch mode

Re-generate automatically when the source file changes:

```bash
glyphkit --source icon.png --platforms ios --no-prompt --watch
```

## Web UI

`glyphkit --ui` starts a local server and opens your browser.

Features:

- Drag-and-drop or click to upload
- Live size and shape previews
- Padding slider with real-time preview
- Background fill: solid color or gradient (linear/radial, 4 directions)
- Platform selection with visual feedback
- Expandable results with icon grid
- Click any icon for full-size preview
- Download ZIP or open output folder

## Development

```bash
uv sync --extra ui --extra dev
uv run pytest -v
```

82 tests covering core, all 6 platforms, CLI, and web API.

## License

MIT
