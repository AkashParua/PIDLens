"""Watch a workspace for new/changed image and label files.

Emits a Qt signal whenever anything inside `images/` or `labels/` changes; the
consumer (MainWindow / Triage / Parse) is responsible for debouncing and
re-running Workspace.scan().
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from pidlens.config import IMAGE_EXTS


class _Handler(FileSystemEventHandler):
    def __init__(self, callback) -> None:
        super().__init__()
        self.callback = callback

    def _maybe(self, path: str) -> None:
        ext = Path(path).suffix.lower()
        if ext in IMAGE_EXTS or ext == ".txt" or path.endswith("data.yaml"):
            self.callback()

    def on_created(self, event):
        if not event.is_directory:
            self._maybe(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._maybe(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self._maybe(event.src_path)


class WorkspaceWatcher(QObject):
    """Coalesces filesystem events to a single `changed` emission per debounce window."""

    changed = pyqtSignal()

    def __init__(self, root: Path, debounce_ms: int = 250, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.root = root
        self._observer: Observer | None = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(debounce_ms)
        self._timer.timeout.connect(self.changed)

    def start(self) -> None:
        if self._observer is not None:
            return
        handler = _Handler(self._on_event)
        self._observer = Observer()
        self._observer.schedule(handler, str(self.root), recursive=True)
        self._observer.start()

    def stop(self) -> None:
        if self._observer is None:
            return
        self._observer.stop()
        self._observer.join(timeout=1.0)
        self._observer = None

    def _on_event(self) -> None:
        # watchdog calls this from a non-Qt thread; QTimer.start() is thread-safe.
        self._timer.start()
