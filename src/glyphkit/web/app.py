"""FastAPI application for glyphkit web UI."""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import zipfile
from contextlib import asynccontextmanager
from io import BytesIO

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

from glyphkit.core import has_transparency
from glyphkit.platforms import PLATFORM_REGISTRY, VALID_PLATFORMS


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    _cleanup_output()


app = FastAPI(title="glyphkit", lifespan=lifespan)

_current_output_dir: pathlib.Path | None = None

STATIC_DIR = pathlib.Path(__file__).parent / "static"
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB


def _cleanup_output() -> None:
    """Remove the current output directory if it exists."""
    global _current_output_dir
    if _current_output_dir and _current_output_dir.exists():
        shutil.rmtree(_current_output_dir, ignore_errors=True)
    _current_output_dir = None


def _open_uploaded_image(data: bytes) -> Image.Image:
    """Open an uploaded image, auto-converting to RGBA."""
    try:
        img = Image.open(BytesIO(data))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not open image file")
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    return img


@app.post("/api/validate")
async def validate_image(image: UploadFile = File(...)) -> JSONResponse:
    """Validate an uploaded image and return metadata."""
    data = await image.read()
    if len(data) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Upload too large (max 50MB)")

    img = _open_uploaded_image(data)
    w, h = img.size
    warnings_list: list[str] = []

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

    img = _open_uploaded_image(data)
    w, h = img.size
    if w != h:
        raise HTTPException(status_code=400, detail=f"Image must be square, got {w}×{h}")

    _cleanup_output()
    _current_output_dir = pathlib.Path(tempfile.mkdtemp(prefix="glyphkit-"))

    options = {"android_bg": android_bg}
    result: dict = {"platforms": {}}

    for platform_name in platform_list:
        platform_dir = _current_output_dir / platform_name
        generator = PLATFORM_REGISTRY[platform_name]
        files = generator(img, platform_dir, options)

        file_entries = []
        for f in files:
            rel = f.relative_to(_current_output_dir)
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
        headers={"Content-Disposition": "attachment; filename=glyphkit-output.zip"},
    )


@app.post("/api/open-folder")
async def open_folder() -> JSONResponse:
    """Copy output to persistent location and open in file explorer."""
    if not _current_output_dir or not _current_output_dir.exists():
        raise HTTPException(status_code=404, detail="No generation output available")

    persistent_dir = pathlib.Path.cwd() / "glyphkit-output"
    if persistent_dir.exists():
        shutil.rmtree(persistent_dir)
    shutil.copytree(_current_output_dir, persistent_dir)

    if sys.platform == "darwin":
        subprocess.Popen(["open", str(persistent_dir)])
    elif sys.platform == "linux":
        subprocess.Popen(["xdg-open", str(persistent_dir)])
    elif sys.platform == "win32":
        subprocess.Popen(["explorer", str(persistent_dir)])

    return JSONResponse({"status": "ok", "path": str(persistent_dir)})


app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
