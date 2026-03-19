"""Server startup for glyphkit web UI."""

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
    import threading

    import uvicorn

    port = _find_free_port()
    url = f"http://127.0.0.1:{port}"
    print(f"glyphkit web UI starting at {url}")

    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    uvicorn.run(
        "glyphkit.web.app:app",
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )
