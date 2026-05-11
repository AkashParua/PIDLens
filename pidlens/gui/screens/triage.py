"""Screen 2 — Image triage (wireframe V1: status-badge grid).

Shows all workspace images in a thumbnail grid, colored by annotation state.
Filter chips toggle which subset is visible. Double-click (or Enter) jumps to
the Annotation screen with the clicked image pre-selected.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QThreadPool
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pidlens.config import get_settings
from pidlens.core.utils import numpy_to_pixmap
from pidlens.core.workers.io_worker import ThumbnailLoadTask
from pidlens.data.workspace import ImageEntry, Workspace
from pidlens.gui.screens._base import Screen


# Status palette — used by both the badge and the tile border tint.
COLOR_ANNOT = QColor("#3a8a4a")     # green
COLOR_UNANNOT = QColor("#c96442")   # warm accent — flags missing work
COLOR_ORPHAN = QColor("#b8852a")    # amber
COLOR_NEUTRAL = QColor("#9a9388")


class FilterBar(QWidget):
    """Row of pill buttons: All · Annotated · Un-annotated."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        for i, label in enumerate(("All", "Annotated", "Un-annotated")):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setObjectName("filter-pill")
            if i == 0:
                btn.setChecked(True)
            lay.addWidget(btn)
            self.group.addButton(btn, i)
        lay.addStretch(1)

    @property
    def current(self) -> str:
        idx = self.group.checkedId()
        return ("all", "annotated", "unannotated")[idx] if idx >= 0 else "all"


def _make_badge_pixmap(thumb: QPixmap, status: str) -> QPixmap:
    """Composite a small status badge on the bottom-left of the thumb."""
    out = QPixmap(thumb)
    painter = QPainter(out)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    diameter = 14
    margin = 6
    if status == "annotated":
        color = COLOR_ANNOT
        char = "✓"
    elif status == "unannotated":
        color = COLOR_UNANNOT
        char = "○"
    else:
        color = COLOR_NEUTRAL
        char = "·"
    painter.setBrush(color)
    painter.setPen(QColor(255, 255, 255, 220))
    painter.drawEllipse(margin, out.height() - margin - diameter, diameter, diameter)
    painter.setPen(QColor(255, 255, 255))
    painter.drawText(
        margin, out.height() - margin - diameter, diameter, diameter,
        Qt.AlignmentFlag.AlignCenter, char,
    )
    painter.end()
    return out


class TriageScreen(Screen):
    title = "Triage"

    def _build(self) -> None:
        self.workspace: Workspace | None = None
        self.pool = QThreadPool.globalInstance()
        self._thumb_cache: dict[Path, QPixmap] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # ── header row: title + filter + counts ──────────────
        header = QHBoxLayout()
        header.setSpacing(12)
        title = QLabel("Image triage")
        title.setObjectName("screen-title")
        header.addWidget(title)
        header.addStretch(1)
        self.summary = QLabel("no workspace")
        self.summary.setObjectName("muted")
        header.addWidget(self.summary)
        root.addLayout(header)

        self.filter_bar = FilterBar()
        self.filter_bar.group.buttonClicked.connect(lambda *_: self._refresh_grid())
        root.addWidget(self.filter_bar)

        # ── grid ─────────────────────────────────────────────
        self.grid = QListWidget()
        self.grid.setObjectName("triage-grid")
        self.grid.setViewMode(QListWidget.ViewMode.IconMode)
        self.grid.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.grid.setMovement(QListWidget.Movement.Static)
        self.grid.setSpacing(8)
        self.grid.setUniformItemSizes(True)
        self.grid.setIconSize(QSize(160, 120))
        self.grid.setGridSize(QSize(180, 165))
        self.grid.setWordWrap(True)
        self.grid.itemDoubleClicked.connect(self._open_in_annotation)
        self.grid.itemActivated.connect(self._open_in_annotation)
        root.addWidget(self.grid, 1)

        self.signals.workspaceOpened.connect(self._on_workspace_opened)
        self.signals.annotationsChanged.connect(self._on_annotations_changed)

    # ─────────────────────────────────────────────────────────
    def _on_workspace_opened(self, ws: Workspace) -> None:
        self.workspace = ws
        self._refresh_grid()

    def _on_annotations_changed(self, _path) -> None:
        if self.workspace is None:
            return
        # Cheap: just re-derive status from the workspace state.
        self.workspace.scan()
        self._refresh_grid()

    def _refresh_grid(self) -> None:
        self.grid.clear()
        if self.workspace is None:
            self.summary.setText("no workspace")
            return

        ws = self.workspace
        flt = self.filter_bar.current
        visible: list[ImageEntry] = []
        for entry in ws.images:
            if flt == "annotated" and not entry.has_label:
                continue
            if flt == "unannotated" and entry.has_label:
                continue
            visible.append(entry)

        self.summary.setText(
            f"{len(visible)} shown · {ws.annotated} annotated · "
            f"{ws.unannotated} un-annotated · {len(ws.orphan_labels)} orphan"
        )

        # Pre-create items with a neutral placeholder icon, schedule thumbnail
        # loads in the background; each task updates its item when finished.
        thumb_max = get_settings().thumbnail_size
        for entry in visible:
            status = "annotated" if entry.has_label else "unannotated"
            item = QListWidgetItem(entry.image.name)
            item.setData(Qt.ItemDataRole.UserRole, entry.image)
            item.setData(Qt.ItemDataRole.UserRole + 1, status)
            item.setToolTip(str(entry.image))
            if entry.image in self._thumb_cache:
                item.setIcon(QIcon(_make_badge_pixmap(self._thumb_cache[entry.image], status)))
            else:
                placeholder = QPixmap(160, 120)
                placeholder.fill(QColor("#e6e2da"))
                item.setIcon(QIcon(_make_badge_pixmap(placeholder, status)))
            self.grid.addItem(item)
            self._schedule_thumbnail(entry.image, status, item, thumb_max)

    def _schedule_thumbnail(self, path: Path, status: str, item: QListWidgetItem, max_side: int) -> None:
        if path in self._thumb_cache:
            return
        task = ThumbnailLoadTask(path, max_side=max(max_side, 160))
        task.signals.finished.connect(
            lambda p, arr, _item=item, _status=status: self._on_thumb_ready(p, arr, _item, _status)
        )
        self.pool.start(task)

    def _on_thumb_ready(self, path: Path, arr, item: QListWidgetItem, status: str) -> None:
        pix = numpy_to_pixmap(arr)
        self._thumb_cache[path] = pix
        # `item` reference is still valid as long as workspace hasn't reloaded.
        # If it has, we silently drop the late result.
        try:
            item.setIcon(QIcon(_make_badge_pixmap(pix, status)))
        except RuntimeError:
            pass

    def _open_in_annotation(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path is None:
            return
        self.signals.imageSelected.emit(path)
        self.signals.requestScreen.emit("annot")
