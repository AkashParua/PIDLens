"""Stateless helpers used across GUI + workers."""

from __future__ import annotations

import numpy as np
from PyQt6.QtGui import QImage, QPixmap


def numpy_to_qimage(arr: np.ndarray) -> QImage:
    """Convert an HxWxC uint8 BGR/BGRA or HxW uint8 grayscale array to QImage.

    cv2 reads BGR by default; we swap to RGB inside this helper so callers
    don't have to remember. The returned QImage owns its own copy of the data
    (.copy()) — without it the QImage references the numpy buffer, which can
    be freed while Qt is still painting from it.
    """
    if arr.ndim == 2:
        h, w = arr.shape
        return QImage(arr.data, w, h, w, QImage.Format.Format_Grayscale8).copy()

    h, w, c = arr.shape
    if c == 3:
        rgb = arr[:, :, ::-1].copy()
        return QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888).copy()
    if c == 4:
        # BGRA → RGBA
        rgba = arr[:, :, [2, 1, 0, 3]].copy()
        return QImage(rgba.data, w, h, 4 * w, QImage.Format.Format_RGBA8888).copy()
    raise ValueError(f"unsupported channel count: {c}")


def numpy_to_pixmap(arr: np.ndarray) -> QPixmap:
    return QPixmap.fromImage(numpy_to_qimage(arr))


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def human_count(n: int) -> str:
    """Compact integer formatting: 1234 → '1.2k', 1_234_567 → '1.2M'."""
    if n < 1000:
        return str(n)
    if n < 1_000_000:
        return f"{n / 1000:.1f}k".rstrip("0").rstrip(".") + ("k" if not f"{n/1000:.1f}".endswith("0") else "")
    return f"{n / 1_000_000:.1f}M"
