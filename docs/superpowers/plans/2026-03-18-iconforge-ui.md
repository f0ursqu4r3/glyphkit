# iconforge Web UI Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local web UI to iconforge so users can drag-and-drop icons, select platforms, and preview results in the browser via `iconforge --ui`.

**Architecture:** FastAPI backend serving REST API + static files. Single-page vanilla JS frontend with dark glassy aesthetic. Reuses existing core.py and platform modules directly.

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, Pillow (existing), vanilla HTML/CSS/JS

**Spec:** `docs/superpowers/specs/2026-03-18-iconforge-ui-design.md`

---

## File Map

| File | Responsibility |
|---|---|
| `pyproject.toml` | Add `ui` optional dependency group |
| `src/iconforge/cli.py` | Add `--ui` flag and server launch |
| `src/iconforge/web/__init__.py` | Package init |
| `src/iconforge/web/app.py` | FastAPI app, all API endpoints |
| `src/iconforge/web/server.py` | Port selection, browser open, uvicorn launch |
| `src/iconforge/web/static/index.html` | Single-page frontend — HTML + CSS + JS |
| `tests/test_web_api.py` | Tests for all API endpoints |

---

## Task 1: Dependencies + Web Package Scaffold

**Files:**
- Modify: `pyproject.toml`
- Create: `src/iconforge/web/__init__.py`
- Create: `src/iconforge/web/app.py` (minimal)
- Create: `src/iconforge/web/server.py`
- Modify: `src/iconforge/cli.py`

- [ ] **Step 1: Add UI optional dependencies to pyproject.toml**

Add to `pyproject.toml` under `[project.optional-dependencies]`:
```toml
ui = ["fastapi>=0.110", "uvicorn>=0.27"]
```

- [ ] **Step 2: Install UI dependencies**

Run: `uv sync --extra ui --extra dev`
Expected: fastapi and uvicorn installed

- [ ] **Step 3: Create web package**

`src/iconforge/web/__init__.py`:
```python
"""iconforge web UI."""
```

`src/iconforge/web/app.py`:
```python
"""FastAPI application for iconforge web UI."""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import zipfile
from io import BytesIO

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

from iconforge.core import has_transparency
from iconforge.platforms import PLATFORM_REGISTRY, VALID_PLATFORMS

# Lifespan context manager (replaces deprecated @app.on_event)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    _cleanup_output()

app = FastAPI(title="iconforge", lifespan=lifespan)

# State: current output directory (managed per generation)
_current_output_dir: pathlib.Path | None = None

STATIC_DIR = pathlib.Path(__file__).parent / "static"
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB


def _cleanup_output() -> None:
    """Remove the current output directory if it exists."""
    global _current_output_dir
    if _current_output_dir and _current_output_dir.exists():
        shutil.rmtree(_current_output_dir, ignore_errors=True)
    _current_output_dir = None


@app.post("/api/validate")
async def validate_image(image: UploadFile = File(...)) -> JSONResponse:
    """Validate an uploaded image and return metadata."""
    data = await image.read()
    if len(data) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Upload too large (max 50MB)")

    try:
        img = Image.open(BytesIO(data))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not open image file")

    w, h = img.size
    warnings_list: list[str] = []

    if img.format != "PNG":
        raise HTTPException(status_code=400, detail=f"Unsupported format: {img.format}. Only PNG is supported.")

    if w != h:
        raise HTTPException(status_code=400, detail=f"Image must be square, got {w}×{h}")

    if w < 1024:
        warnings_list.append(f"Image is {w}×{h}, 1024×1024 recommended for best quality")

    transparent = has_transparency(img)
    if transparent:
        warnings_list.append("Image has transparency. iOS does not support transparent app icons.")

    return JSONResponse({
        "width": w,
        "height": h,
        "is_square": w == h,
        "has_transparency": transparent,
        "warnings": warnings_list,
    })


@app.post("/api/generate")
async def generate_icons(
    image: UploadFile = File(...),
    platforms: str = Form(...),
    android_bg: str = Form("#FFFFFF"),
) -> JSONResponse:
    """Generate icons for selected platforms."""
    global _current_output_dir

    data = await image.read()
    if len(data) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Upload too large (max 50MB)")

    try:
        platform_list = json.loads(platforms)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid JSON in platforms field")

    if not isinstance(platform_list, list) or not platform_list:
        raise HTTPException(status_code=400, detail="platforms must be a non-empty list")

    invalid = [p for p in platform_list if p not in PLATFORM_REGISTRY]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid platform(s): {', '.join(invalid)}")

    try:
        img = Image.open(BytesIO(data))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not open image file")

    w, h = img.size
    if img.format != "PNG":
        raise HTTPException(status_code=400, detail=f"Unsupported format: {img.format}. Only PNG is supported.")
    if w != h:
        raise HTTPException(status_code=400, detail=f"Image must be square, got {w}×{h}")

    # Clean up previous generation
    _cleanup_output()
    _current_output_dir = pathlib.Path(tempfile.mkdtemp(prefix="iconforge-"))

    options = {"android_bg": android_bg}
    result: dict = {"platforms": {}}

    for platform_name in platform_list:
        platform_dir = _current_output_dir / platform_name
        generator = PLATFORM_REGISTRY[platform_name]
        files = generator(img, platform_dir, options)

        file_entries = []
        for f in files:
            rel = f.relative_to(_current_output_dir)
            # Get pixel dimensions for image files
            px_size = 0
            if f.suffix.lower() in (".png", ".ico", ".icns"):
                try:
                    with Image.open(f) as im:
                        px_size = im.size[0]
                except Exception:
                    pass
            file_entries.append({
                "name": f.name,
                "size": px_size,
                "preview_url": f"/api/preview/{rel}",
            })

        result["platforms"][platform_name] = {
            "file_count": len(files),
            "files": file_entries,
        }

    return JSONResponse(result)


@app.get("/api/preview/{platform}/{path:path}")
async def preview_file(platform: str, path: str) -> FileResponse:
    """Serve a generated file for preview."""
    if not _current_output_dir:
        raise HTTPException(status_code=404, detail="No generation output available")

    file_path = _current_output_dir / platform / path
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # Security: ensure path doesn't escape output dir
    try:
        file_path.resolve().relative_to(_current_output_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(file_path)


@app.get("/api/download")
async def download_zip() -> StreamingResponse:
    """Zip the output directory and stream it."""
    if not _current_output_dir or not _current_output_dir.exists():
        raise HTTPException(status_code=404, detail="No generation output available")

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in _current_output_dir.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(_current_output_dir)
                zf.write(file, arcname)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=iconforge-output.zip"},
    )


@app.post("/api/open-folder")
async def open_folder() -> JSONResponse:
    """Copy output to persistent location and open in file explorer."""
    if not _current_output_dir or not _current_output_dir.exists():
        raise HTTPException(status_code=404, detail="No generation output available")

    persistent_dir = pathlib.Path.cwd() / "iconforge-output"
    if persistent_dir.exists():
        shutil.rmtree(persistent_dir)
    shutil.copytree(_current_output_dir, persistent_dir)

    # Open in native file explorer
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(persistent_dir)])
    elif sys.platform == "linux":
        subprocess.Popen(["xdg-open", str(persistent_dir)])
    elif sys.platform == "win32":
        subprocess.Popen(["explorer", str(persistent_dir)])

    return JSONResponse({"status": "ok", "path": str(persistent_dir)})


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
```

`src/iconforge/web/server.py`:
```python
"""Server startup for iconforge web UI."""

from __future__ import annotations

import socket
import webbrowser


def _find_free_port() -> int:
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_server() -> None:
    """Start the web UI server and open the browser."""
    import uvicorn

    port = _find_free_port()
    url = f"http://127.0.0.1:{port}"
    print(f"iconforge web UI starting at {url}")

    # Open browser after a short delay (uvicorn blocks, so use a callback)
    import threading
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    uvicorn.run(
        "iconforge.web.app:app",
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )
```

- [ ] **Step 4: Add --ui flag to CLI**

Modify `src/iconforge/cli.py` — add argument and handler:

Add to `parse_args()`:
```python
parser.add_argument("--ui", action="store_true", help="Launch web UI")
```

Add at the start of `main()`, before `if args.no_prompt:`:
```python
if args.ui:
    try:
        from iconforge.web.server import start_server
    except ImportError:
        print(
            "Error: Web UI requires extra dependencies. "
            "Install with: uv pip install -e '.[ui]'",
            file=sys.stderr,
        )
        sys.exit(1)
    start_server()
    return
```

- [ ] **Step 5: Create a placeholder index.html**

`src/iconforge/web/static/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>iconforge</title>
</head>
<body>
    <h1>iconforge</h1>
    <p>Web UI coming soon.</p>
</body>
</html>
```

- [ ] **Step 6: Verify server starts**

Run: `uv run iconforge --ui`
Expected: prints URL, opens browser showing placeholder page. Ctrl+C to stop.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml src/iconforge/web/ src/iconforge/cli.py uv.lock
git commit -m "feat: web UI scaffold with FastAPI, all API endpoints, --ui flag"
```

---

## Task 2: API Endpoint Tests (TDD)

**Files:**
- Create: `tests/test_web_api.py`

- [ ] **Step 1: Write API tests**

`tests/test_web_api.py`:
```python
"""Tests for iconforge web API endpoints."""

from __future__ import annotations

import json
import pathlib
from io import BytesIO

import pytest
from PIL import Image

from iconforge.web.app import app, _cleanup_output

# Import TestClient conditionally
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
        # Generate first
        gen_resp = client.post(
            "/api/generate",
            files={"image": ("icon.png", png_bytes, "image/png")},
            data={"platforms": '["linux"]', "android_bg": "#FFFFFF"},
        )
        # Use a preview_url from the response
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
```

- [ ] **Step 2: Run tests**

Run: `uv run pytest tests/test_web_api.py -v`
Expected: all tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_web_api.py
git commit -m "test: web API endpoint tests"
```

---

## Task 3: Frontend — HTML Structure + CSS Theme

**Files:**
- Modify: `src/iconforge/web/static/index.html`

This is the big task — the entire single-page frontend. Due to its size, this task focuses on the HTML structure and CSS only. JS interactivity comes in Task 4.

- [ ] **Step 1: Write the complete HTML + CSS**

Replace `src/iconforge/web/static/index.html` with the full page. The HTML contains:

1. Header with "iconforge" wordmark
2. Drop zone (drag-and-drop area)
3. Image info bar (hidden initially)
4. Live preview strip (hidden initially)
5. Platform selector grid (6 cards)
6. Android options panel (hidden initially)
7. Generate button (disabled initially)
8. Results section (hidden initially)

All CSS is inline in a `<style>` tag. The theme uses:
- `#0a0a0f` base background
- Frosted glass panels: `rgba(255,255,255,0.03)` bg + `backdrop-filter: blur(20px)`
- `#6366f1` → `#8b5cf6` accent gradient
- `#e2e8f0` primary text, `#94a3b8` secondary
- Monospace font stack for accents
- Smooth 150ms transitions
- Checkered background pattern for preview strip (CSS gradient)
- Pulsing border animation on drop zone dragover
- Staggered fade-in for results cards

The JS section is a placeholder `<script>` tag with `// JS in Task 4` comment.

**NOTE TO IMPLEMENTER:** This HTML file will be large (~400-600 lines). That is expected for a single-page app with inline CSS. Focus on getting the visual design right — the dark glassy aesthetic, the layout, the micro-interactions via CSS. Use the spec's theme section as the exact reference. The JS interactivity will be added in Task 4.

Key CSS details:
- Drop zone: `min-height: 300px`, dashed `2px` border, `border-radius: 16px`, transitions to accent glow on `.dragover` class
- Platform cards: CSS grid `grid-template-columns: repeat(3, 1fr)` at desktop, `repeat(2, 1fr)` at mobile. Each card is a glass panel with emoji icon, name, description. `.selected` class adds accent border + subtle box-shadow glow
- Generate button: `height: 48px`, full-width, gradient background, `border-radius: 8px`, `transform: scale(1.01)` on hover. `.disabled` class grays it out. `.loading` class shows a pulse animation
- Results: hidden by default. Summary bar is a glass panel with flex layout. Platform result cards are collapsible — chevron rotates on expand
- Preview strip: horizontal scroll, items sized at actual pixel size (capped at display 64px), checkered background via CSS repeating-conic-gradient
- Responsive: single column under 768px

- [ ] **Step 2: Verify page loads with theme**

Run: `uv run iconforge --ui`
Expected: browser shows the full layout with dark glassy theme. Nothing is interactive yet (JS not implemented), but all sections are visible for inspection. Ctrl+C to stop.

- [ ] **Step 3: Commit**

```bash
git add src/iconforge/web/static/index.html
git commit -m "feat: web UI frontend — HTML structure and dark glassy CSS theme"
```

---

## Task 4: Frontend — JavaScript Interactivity

**Files:**
- Modify: `src/iconforge/web/static/index.html` (replace JS placeholder)

- [ ] **Step 1: Implement all JavaScript**

Replace the `// JS in Task 4` placeholder in `index.html` with the full interactivity. The JS handles:

**State:**
```javascript
let selectedPlatforms = new Set();
let imageFile = null;
let generationResult = null;
```

**Drop zone:**
- `dragover`/`dragleave`/`drop` events on the drop zone element
- Also a hidden `<input type="file" accept=".png">` triggered by click on the drop zone
- On file drop/select: validate via `POST /api/validate`, show image preview + metadata
- Show the image as a data URL in an `<img>` tag inside the drop zone
- Show dimensions badge and transparency warning if applicable
- Show "Change image" link that resets the drop zone
- Show live preview strip: create `<img>` elements at sizes 16, 32, 64, 128, 256, 512 using the same data URL, CSS-sized

**Platform selector:**
- Click handler on each platform card toggles `.selected` class and updates `selectedPlatforms` set
- "Select All / Deselect All" link toggles all
- When Android is toggled, show/hide the options panel with a CSS transition

**Generate button:**
- Enabled only when `imageFile !== null && selectedPlatforms.size > 0`
- On click: `POST /api/generate` with FormData (image file, platforms JSON, android_bg)
- During generation: button shows "Generating..." with loading animation
- On success: populate results section and show it with slide-down animation

**Results section:**
- Summary bar: total file count across all platforms, "Download ZIP" link (`/api/download`), "Open Folder" button (`POST /api/open-folder`)
- Platform cards: render one per platform from response. Click to expand/collapse
- Expanded view: render icon grid. Each icon is an `<img>` with `src` set to the `preview_url` from the response. Display at actual size capped at 128px. Show pixel dimensions label below each

**Error handling:**
- API errors show a toast notification (absolute positioned, top-right, auto-dismiss after 5s)
- Network errors show a generic "Connection error" toast

- [ ] **Step 2: Test the full flow end-to-end manually**

Run: `uv run iconforge --ui`
Test flow:
1. Drag a PNG onto the drop zone → should show preview + metadata
2. Select platforms → cards highlight
3. Click Generate → should show loading, then results
4. Expand a platform card → should show icon grid with previews
5. Click Download ZIP → should download a zip file
6. Test with a non-square image → should show error toast

- [ ] **Step 3: Commit**

```bash
git add src/iconforge/web/static/index.html
git commit -m "feat: web UI JavaScript — drag-and-drop, generation, results display"
```

---

## Task 5: Polish + Integration Test

**Files:**
- Modify: `src/iconforge/web/static/index.html` (polish pass)
- Run: full test suite

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest -v`
Expected: all tests pass (existing 49 + new web API tests)

- [ ] **Step 2: Visual polish pass**

Run `uv run iconforge --ui` and check:
- Drop zone glow animation on dragover
- Platform card selection glow
- Generate button hover effect
- Results fade-in animation
- Icon grid layout at various platform counts
- Responsive layout under 768px (resize browser)

Fix any visual issues found.

- [ ] **Step 3: Commit any polish fixes**

```bash
git add src/iconforge/web/static/index.html
git commit -m "fix: web UI visual polish and responsive fixes"
```

- [ ] **Step 4: Run full test suite one final time**

Run: `uv run pytest -v`
Expected: all tests pass

- [ ] **Step 5: Final commit if needed**

```bash
git add -A
git commit -m "chore: final web UI cleanup"
```
