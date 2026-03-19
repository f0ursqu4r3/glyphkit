"""Watch mode: re-generate on source file change."""

from __future__ import annotations

import pathlib
import time
from typing import Callable


def watch_file(path: pathlib.Path, on_change: Callable[[], None]) -> None:
    """Poll a file for changes and call on_change when modified.

    Blocks until KeyboardInterrupt (Ctrl+C).
    """
    print(f"\nWatching {path} for changes... (Ctrl+C to stop)")

    last_mtime = path.stat().st_mtime

    try:
        while True:
            time.sleep(1)
            try:
                current_mtime = path.stat().st_mtime
            except FileNotFoundError:
                continue

            if current_mtime != last_mtime:
                last_mtime = current_mtime
                print(f"\n{path.name} changed, regenerating...")
                try:
                    on_change()
                except Exception as e:
                    print(f"Error during regeneration: {e}")
    except KeyboardInterrupt:
        print("\nWatch stopped.")
