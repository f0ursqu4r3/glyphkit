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

| Flag | Default | Description |
|---|---|---|
| `--source` | — | Path to source PNG (1024×1024 recommended) |
| `--platforms` | — | Comma-separated: ios, android, macos, windows, web, linux |
| `--output-dir` | `./iconforge-output` | Output directory |
| `--android-bg` | `#FFFFFF` | Android adaptive icon background color |
| `--no-prompt` | false | Skip interactive prompts (for CI) |

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
