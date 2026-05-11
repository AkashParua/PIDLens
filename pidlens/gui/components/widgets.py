"""Reusable building blocks used across screens.

These are intentionally small QWidget subclasses with a flat API; styling comes
from the global QSS (object names matter — they're the QSS selectors).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class StatBlock(QFrame):
    """A small labeled metric card. Used in Parse stats, Training KPIs, etc."""

    def __init__(
        self,
        label: str,
        value: str = "—",
        sub: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("stat-block")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(2)

        self._label = QLabel(label)
        self._label.setObjectName("stat-label")
        self._value = QLabel(value)
        self._value.setObjectName("stat-value")
        self._sub = QLabel(sub)
        self._sub.setObjectName("stat-sub")

        big = QFont()
        big.setPointSize(18)
        big.setWeight(QFont.Weight.DemiBold)
        self._value.setFont(big)

        lay.addWidget(self._label)
        lay.addWidget(self._value)
        lay.addWidget(self._sub)

    def set_value(self, value: str) -> None:
        self._value.setText(value)

    def set_sub(self, sub: str) -> None:
        self._sub.setText(sub)


class Section(QFrame):
    """Titled bordered panel. Body is a QVBoxLayout exposed as `.body`."""

    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("section")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        if title:
            head = QLabel(title)
            head.setObjectName("section-head")
            head.setContentsMargins(12, 8, 12, 8)
            outer.addWidget(head)

        body_w = QWidget()
        self.body = QVBoxLayout(body_w)
        self.body.setContentsMargins(12, 12, 12, 12)
        self.body.setSpacing(8)
        outer.addWidget(body_w, 1)


class Chip(QLabel):
    """Pill-shaped status tag."""

    def __init__(self, text: str, *, kind: str = "neutral", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("chip")
        self.setProperty("kind", kind)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


def primary_button(text: str, parent: QWidget | None = None) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setProperty("primary", True)
    return btn
