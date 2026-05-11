"""Minimal painted charts so we don't pull QtCharts in for a few visuals.

Both widgets are pure custom paintEvent — no animation, no interactivity. They
look fine, and they avoid a 30 MB dependency for something this simple.
"""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget

# Match the canvas class palette so the split visuals stay coherent across screens.
from pidlens.gui.canvas import class_color


SPLIT_COLORS = {
    "train": QColor("#3a8a4a"),
    "val": QColor("#c96442"),
    "test": QColor("#5b6dc9"),
}


class DonutChart(QWidget):
    """Three-segment donut: train / val / test counts."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(220, 220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._counts = {"train": 0, "val": 0, "test": 0}

    def set_counts(self, train: int, val: int, test: int) -> None:
        self._counts = {"train": train, "val": val, "test": test}
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(self.width(), self.height()) - 20
        x = (self.width() - side) / 2
        y = (self.height() - side) / 2
        rect = QRectF(x, y, side, side)
        total = sum(self._counts.values())
        if total == 0:
            p.setPen(QPen(QColor("#9a9388"), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(rect)
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, "no data")
            return
        start = 90 * 16  # 12 o'clock
        for key in ("train", "val", "test"):
            value = self._counts[key]
            if value == 0:
                continue
            span = -int(round(value / total * 360 * 16))
            p.setBrush(SPLIT_COLORS[key])
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPie(rect, start, span)
            start += span
        # punch the hole
        inner = rect.adjusted(side * 0.18, side * 0.18, -side * 0.18, -side * 0.18)
        p.setBrush(self.palette().window())
        p.drawEllipse(inner)
        # centre text
        p.setPen(QPen(QColor("#29261b")))
        f = QFont()
        f.setPointSize(16)
        f.setWeight(QFont.Weight.DemiBold)
        p.setFont(f)
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{total}\nimages")


class StackedClassBars(QWidget):
    """Horizontal stacked bars: one row per class, segments train/val/test."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(280, 120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._rows: list[tuple[str, tuple[int, int, int]]] = []

    def set_rows(self, rows: list[tuple[str, tuple[int, int, int]]]) -> None:
        self._rows = rows
        self.setMinimumHeight(max(120, 30 * max(1, len(rows))))
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self._rows:
            p.setPen(QPen(QColor("#9a9388")))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "no classes")
            return
        margin_left = 90
        margin_right = 50
        row_h = 18
        gap = 6
        max_total = max(sum(counts) for _, counts in self._rows) or 1
        avail = max(10, self.width() - margin_left - margin_right)
        y = 8
        f = QFont()
        f.setPointSize(10)
        p.setFont(f)
        for label, (tr, va, te) in self._rows:
            total = tr + va + te
            # left label
            p.setPen(QPen(QColor("#4a4438")))
            p.drawText(
                QRectF(0, y, margin_left - 6, row_h),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                label[:14],
            )
            # bar segments
            x = margin_left
            for key, value in (("train", tr), ("val", va), ("test", te)):
                w = (value / max_total) * avail
                p.setBrush(SPLIT_COLORS[key])
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRect(QRectF(x, y, w, row_h))
                x += w
            # right total
            p.setPen(QPen(QColor("#7a7165")))
            p.drawText(
                QRectF(margin_left + avail + 4, y, margin_right - 4, row_h),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                str(total),
            )
            y += row_h + gap


class Sparkline(QWidget):
    """Single-line chart for live training metrics."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._values: list[float] = []
        self._title = ""
        self._color = QColor("#c96442")

    def set_series(self, title: str, values: list[float], color: QColor | None = None) -> None:
        self._title = title
        self._values = list(values)
        if color is not None:
            self._color = color
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(8, 18, -8, -8)
        # title
        p.setPen(QPen(QColor("#4a4438")))
        f = QFont()
        f.setPointSize(10)
        f.setWeight(QFont.Weight.DemiBold)
        p.setFont(f)
        p.drawText(0, 14, self._title)
        # frame
        p.setPen(QPen(QColor("#d8d2c5")))
        p.drawRect(rect)
        if len(self._values) < 2:
            return
        lo = min(self._values)
        hi = max(self._values)
        span = max(1e-6, hi - lo)
        # value text
        p.setPen(QPen(QColor("#7a7165")))
        p.drawText(self.width() - 80, 14, f"{self._values[-1]:.3f}")
        # line
        pen = QPen(self._color)
        pen.setWidthF(2.0)
        p.setPen(pen)
        n = len(self._values)
        prev = None
        for i, v in enumerate(self._values):
            x = rect.left() + (i / max(1, n - 1)) * rect.width()
            y = rect.bottom() - ((v - lo) / span) * rect.height()
            point = QPointF(x, y)
            if prev is not None:
                p.drawLine(prev, point)
            prev = point
