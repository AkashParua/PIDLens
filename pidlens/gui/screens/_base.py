"""Shared base class for all top-level screens."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from pidlens.core.signals import AppSignals


class Screen(QWidget):
    """Subclasses receive `signals=` from MainWindow.

    Override `_build` to construct the UI; `signals` is already wired by then.
    """

    title: str = ""

    def __init__(self, *, signals: AppSignals, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.signals = signals
        self._build()

    def _build(self) -> None:  # override in subclasses
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(QLabel(f"{self.title or self.__class__.__name__} — placeholder"))
