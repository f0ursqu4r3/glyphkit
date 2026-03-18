# iconforge Web UI — Design Spec

## Overview

A local web UI for iconforge that complements the CLI. Users launch it with `iconforge --ui`, which starts a local FastAPI server and opens the browser. The UI provides drag-and-drop image upload, platform selection, live preview, and a polished results view — all with a dark, glassy, developer-tool aesthetic.

## Architecture

**Backend:** FastAPI app in `src/iconforge/web/` serving a REST API + static files. Reuses existing `core.py` and platform modules directly — no subprocess calls.

**Frontend:** Single HTML page (`index.html`) with inline CSS and vanilla JS. Served by FastAPI's `StaticFiles`. All interactions via `fetch()` to the API.

**Entry:** `iconforge --ui` starts the FastAPI server on a random available port and opens the browser. Ctrl+C stops it.

### New dependencies

Added as optional dependencies under `[project.optional-dependencies] ui = [...]`:

- `fastapi` — API framework
- `uvicorn` — ASGI server

The `--ui` flag gives a helpful error if these are not installed: `"Web UI requires extra dependencies. Install with: uv pip install -e '.[ui]'"`

### Server binding

The server binds to `127.0.0.1` only (never `0.0.0.0`) to prevent LAN exposure. This is a local-only tool.

### Output directory management

The server manages output internally. Each generation creates a new temp directory via `tempfile.mkdtemp(prefix="iconforge-")`. The previous generation's temp directory is cleaned up when a new generation starts, or when the server shuts down. The user retrieves files via `/api/preview` and `/api/download` — the temp path is an internal detail not exposed to the frontend.

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/validate` | Upload image, returns dimensions, transparency info, warnings |
| `POST` | `/api/generate` | Upload image + platform selections + options, triggers generation, returns file manifest |
| `GET` | `/api/preview/{platform}/{path:path}` | Serve a generated icon for in-browser preview |
| `GET` | `/api/download` | Zip and download the entire output directory |
| `POST` | `/api/open-folder` | Open the output directory in the native file explorer |

### Error responses

All endpoints return errors as JSON with an appropriate HTTP status:

```json
{"error": "Image must be square, got 800x600"}
```

Status codes:
- `400` — validation errors (non-PNG, non-square, missing fields)
- `422` — malformed request (bad JSON in platforms field)
- `413` — upload too large (max 50MB)
- `500` — unexpected server error

### `POST /api/validate` request

Multipart form upload with field `image` (PNG file).

Response:
```json
{
  "width": 1024,
  "height": 1024,
  "is_square": true,
  "has_transparency": false,
  "warnings": []
}
```

### `POST /api/generate` request

Multipart form with fields:
- `image` — PNG file
- `platforms` — JSON array string, e.g. `["ios", "android", "web"]`
- `android_bg` — hex color string, e.g. `"#FFFFFF"`

Response:
```json
{
  "platforms": {
    "ios": {
      "file_count": 16,
      "files": [
        {"name": "Icon-20@1x.png", "size": 20, "preview_url": "/api/preview/ios/AppIcon.appiconset/Icon-20@1x.png"}
      ]
    }
  }
}
```

Each file entry includes a ready-to-use `preview_url`. No internal paths are exposed to the frontend.

### `POST /api/open-folder`

Opens the current output directory in the native file explorer. Copies generated files to a persistent location (`./iconforge-output/` in CWD) first, then opens it with `open` (macOS), `xdg-open` (Linux), or `explorer` (Windows).

### `GET /api/preview/{platform}/{path:path}`

Serves the generated file from the output directory. Used by the frontend to display icon previews.

### `GET /api/download`

Creates a zip of the entire output directory and streams it as a download.

## Visual Design

### Theme

- **Base:** `#0a0a0f` background
- **Panels:** Frosted glass — `rgba(255, 255, 255, 0.03)` background, `backdrop-filter: blur(20px)`, `border: 1px solid rgba(255, 255, 255, 0.06)`
- **Accent gradient:** `#6366f1` → `#8b5cf6` (indigo → violet)
- **Text:** `#e2e8f0` primary, `#94a3b8` secondary
- **Monospace accents:** `"SF Mono", "Cascadia Code", "JetBrains Mono", monospace`
- **Border radius:** `12px` panels, `8px` buttons, `16px` drop zone
- **Transitions:** 150ms ease for interactions

### Layout (single page, vertical flow)

1. **Header** — "iconforge" in monospace with subtle gradient text fill. Compact, top-left aligned.

2. **Drop zone** — Large central panel (~300px tall), dashed border (`rgba(255,255,255,0.1)`), centered icon + "Drop your icon here" text. Glows with accent gradient on dragover. After image is loaded: shows image preview (centered, ~200px), dimensions badge, transparency indicator (warning badge if transparent + iOS selected), and a "Change image" link.

3. **Live preview strip** — Appears after image load. Shows the source image rendered at 16, 32, 64, 128, 256, 512px in a horizontal row on a subtle checkered background (to show transparency). Helps the user judge icon quality at small sizes before generating.

4. **Platform selector** — 2×3 grid of glass cards. Each card: platform icon (emoji or SVG), platform name, brief description (e.g., "AppIcon.appiconset + .icns"). Click to toggle selection — selected cards get accent border glow. "Select All / Deselect All" toggle link above the grid.

5. **Options panel** — Visible when Android is selected. Glass panel with:
   - Color picker for Android adaptive icon background (native `<input type="color">` styled to match, default `#FFFFFF`)
   - Hex value display next to picker

6. **Generate button** — Full-width, gradient accent background, white text, 48px tall. Hover: slight scale + glow. Disabled state when no image or no platforms selected. During generation: shows progress text ("Generating iOS icons..." cycling through platforms).

7. **Results section** — Appears after generation with a slide-down animation. Contains:
   - **Summary bar** — total file count, "Download ZIP" button, "Open Folder" button (calls `POST /api/open-folder`)
   - **Platform cards** — one per generated platform. Glass panel showing: platform name, file count, expand/collapse chevron. Collapsed by default.
   - **Expanded view** — icon grid inside the card. Shows each generated icon as a thumbnail at its actual size (capped at 128px display), with pixel dimensions label below. Icons on subtle dark background. Scrollable if many icons.

### Micro-interactions

- Drop zone: dashed border pulses on dragover, accent glow appears
- Platform cards: 150ms border-color + box-shadow transition on select
- Generate button: `transform: scale(1.01)` on hover, gradient shifts
- Results: cards fade in sequentially (50ms stagger)
- Icon grid: thumbnails fade in on expand

## File Structure

```
src/iconforge/web/
  __init__.py
  app.py          # FastAPI app, API endpoints
  server.py       # Server startup logic (port selection, browser open)
  static/
    index.html    # Single page — HTML + CSS + JS
```

## CLI Integration

The `--ui` flag in `cli.py` starts the web server:

```python
parser.add_argument("--ui", action="store_true", help="Launch web UI")
```

In `main()`:
```python
if args.ui:
    from iconforge.web.server import start_server
    start_server()
    return
```

`start_server()` finds an available port, starts uvicorn, and opens the default browser.

## Stretch Goals (post-core)

- Crop/padding tool — canvas-based editor to adjust icon framing before generation
- Per-platform background color/preview — see how the icon looks on iOS springboard, Android launcher, etc.
- Before/after comparisons — original vs. generated at each size
- Drag to reorder platforms in results
- Dark/light mode toggle (default dark)

## Decisions Made

- **Vanilla JS over Vue/React** — single page tool, no build step needed, minimal complexity
- **FastAPI over Flask** — async-ready, modern Python, built-in validation
- **Static files served by FastAPI** — no separate dev server, single process
- **Random port + auto-open browser** — zero configuration for the user
