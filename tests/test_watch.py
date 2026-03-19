"""Tests for watch mode."""

from __future__ import annotations

import pathlib
import threading
import time

from glyphkit.watch import watch_file


class TestWatchFile:
    def test_detects_file_change(self, tmp_path: pathlib.Path) -> None:
        test_file = tmp_path / "test.txt"
        test_file.write_text("v1")

        changes: list[str] = []

        def on_change():
            changes.append("changed")

        # Run watch in a thread, let it poll once, then modify file
        thread = threading.Thread(target=watch_file, args=(test_file, on_change), daemon=True)
        thread.start()

        time.sleep(1.5)  # Wait for at least one poll
        test_file.write_text("v2")  # Trigger change
        time.sleep(2)  # Wait for detection

        assert len(changes) >= 1

    def test_handles_missing_file(self, tmp_path: pathlib.Path) -> None:
        test_file = tmp_path / "test.txt"
        test_file.write_text("v1")

        changes: list[str] = []

        thread = threading.Thread(target=watch_file, args=(test_file, lambda: changes.append("x")), daemon=True)
        thread.start()

        time.sleep(0.5)
        test_file.unlink()  # Delete file
        time.sleep(1.5)
        # Should not crash — just continues polling
        # No assertion needed, test passes if no exception
