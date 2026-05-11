"""Background I/O tasks: image load, thumbnail generation, label save.

Every task is a QRunnable so it can be submitted to a shared QThreadPool. The
emit-signal-from-worker pattern uses a small QObject subclass per task (Qt
disallows signals on a QRunnable directly).
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

from pidlens.data.yolo_parser import YoloBox, write_labels


# ── Image load ────────────────────────────────────────────────
class _ImageLoadSignals(QObject):
    finished = pyqtSignal(object, object)  # path, ndarray (BGR) or None
    failed = pyqtSignal(object, str)       # path, error message


class ImageLoadTask(QRunnable):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path
        self.signals = _ImageLoadSignals()

    def run(self) -> None:
        try:
            # cv2.imread doesn't accept Path; also fails silently on unicode
            # paths in Windows. np.fromfile handles both.
            buf = np.fromfile(str(self.path), dtype=np.uint8)
            img = cv2.imdecode(buf, cv2.IMREAD_UNCHANGED)
            if img is None:
                raise RuntimeError("cv2 returned None")
            self.signals.finished.emit(self.path, img)
        except Exception as e:  # noqa: BLE001
            self.signals.failed.emit(self.path, str(e))


# ── Thumbnail ─────────────────────────────────────────────────
class _ThumbnailSignals(QObject):
    finished = pyqtSignal(object, object)  # path, ndarray (BGR, downscaled)
    failed = pyqtSignal(object, str)


class ThumbnailLoadTask(QRunnable):
    """Decode + downscale to `max_side` pixels on the long edge."""

    def __init__(self, path: Path, max_side: int = 192) -> None:
        super().__init__()
        self.path = path
        self.max_side = max_side
        self.signals = _ThumbnailSignals()

    def run(self) -> None:
        try:
            buf = np.fromfile(str(self.path), dtype=np.uint8)
            img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
            if img is None:
                raise RuntimeError("cv2 returned None")
            h, w = img.shape[:2]
            scale = self.max_side / max(h, w)
            if scale < 1.0:
                img = cv2.resize(
                    img,
                    (max(1, int(w * scale)), max(1, int(h * scale))),
                    interpolation=cv2.INTER_AREA,
                )
            self.signals.finished.emit(self.path, img)
        except Exception as e:  # noqa: BLE001
            self.signals.failed.emit(self.path, str(e))


# ── Label save ────────────────────────────────────────────────
class _LabelSaveSignals(QObject):
    finished = pyqtSignal(object)         # path
    failed = pyqtSignal(object, str)


class LabelSaveTask(QRunnable):
    def __init__(self, path: Path, boxes: Iterable[YoloBox]) -> None:
        super().__init__()
        self.path = path
        self.boxes = list(boxes)
        self.signals = _LabelSaveSignals()

    def run(self) -> None:
        try:
            write_labels(self.path, self.boxes)
            self.signals.finished.emit(self.path)
        except Exception as e:  # noqa: BLE001
            self.signals.failed.emit(self.path, str(e))
