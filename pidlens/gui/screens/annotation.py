"""Screen 3 — Annotation canvas (wireframe V1).

Layout: classes column (L) · canvas (centre) · attrs column (R), with a
thumbstrip across the bottom. Autosave fires 300 ms after the last edit; class
list is mirrored to data.yaml on every change.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QThreadPool, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from pidlens.core.utils import numpy_to_pixmap
from pidlens.core.workers.io_worker import ImageLoadTask, LabelSaveTask, ThumbnailLoadTask
from pidlens.data.workspace import Workspace
from pidlens.data.yolo_parser import YoloBox, read_labels, write_data_yaml
from pidlens.gui.canvas import AnnotationCanvas, BBoxItem, class_color
from pidlens.gui.screens._base import Screen


THUMB_SIZE = 64


class ClassesPanel(QWidget):
    """Left rail: class list with add/rename/delete and active-class radio."""

    activeChanged = pyqtSignal(int)
    classesEdited = pyqtSignal(list)  # full ordered list of class names

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        header = QLabel("Classes")
        header.setObjectName("panel-title")
        lay.addWidget(header)

        self.list = QListWidget()
        self.list.setObjectName("classes-list")
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list.currentRowChanged.connect(self._on_row_changed)
        self.list.itemDoubleClicked.connect(self._on_rename)
        lay.addWidget(self.list, 1)

        row = QHBoxLayout()
        self.add_btn = QPushButton("+")
        self.add_btn.setFixedWidth(28)
        self.add_btn.setToolTip("Add class")
        self.add_btn.clicked.connect(self._on_add)
        self.del_btn = QPushButton("−")
        self.del_btn.setFixedWidth(28)
        self.del_btn.setToolTip("Delete class")
        self.del_btn.clicked.connect(self._on_delete)
        row.addWidget(self.add_btn)
        row.addWidget(self.del_btn)
        row.addStretch(1)
        lay.addLayout(row)

        hint = QLabel("1–9 to assign\nDel to remove box")
        hint.setObjectName("muted")
        lay.addWidget(hint)

        self._names: list[str] = []

    # ── API ───────────────────────────────────────────────────
    def set_names(self, names: list[str]) -> None:
        self._names = list(names) or ["object"]
        self.list.clear()
        for i, name in enumerate(self._names):
            self._add_item(i, name)
        if self.list.count():
            self.list.setCurrentRow(0)

    def names(self) -> list[str]:
        return list(self._names)

    def active_id(self) -> int:
        row = self.list.currentRow()
        return max(0, row)

    # ── internals ─────────────────────────────────────────────
    def _add_item(self, i: int, name: str) -> None:
        item = QListWidgetItem(f"{i}  ·  {name}")
        pix = QPixmap(12, 12)
        pix.fill(class_color(i))
        item.setIcon(QIcon(pix))
        self.list.addItem(item)

    def _on_row_changed(self, row: int) -> None:
        if row >= 0:
            self.activeChanged.emit(row)

    def _on_add(self) -> None:
        name, ok = QInputDialog.getText(self, "New class", "Name:")
        if not ok or not name.strip():
            return
        self._names.append(name.strip())
        self._add_item(len(self._names) - 1, name.strip())
        self.list.setCurrentRow(len(self._names) - 1)
        self.classesEdited.emit(list(self._names))

    def _on_rename(self, item: QListWidgetItem) -> None:
        i = self.list.row(item)
        current = self._names[i] if 0 <= i < len(self._names) else ""
        name, ok = QInputDialog.getText(self, "Rename class", "Name:", text=current)
        if not ok or not name.strip():
            return
        self._names[i] = name.strip()
        item.setText(f"{i}  ·  {name.strip()}")
        self.classesEdited.emit(list(self._names))

    def _on_delete(self) -> None:
        i = self.list.currentRow()
        if i < 0 or i >= len(self._names):
            return
        # Keep at least one class — YOLO requires it.
        if len(self._names) == 1:
            return
        del self._names[i]
        self.list.takeItem(i)
        # Renumber remaining labels.
        for k in range(self.list.count()):
            self.list.item(k).setText(f"{k}  ·  {self._names[k]}")
        self.classesEdited.emit(list(self._names))


class AttrsPanel(QWidget):
    """Right rail: shows the selected box's class + pixel rect."""

    classChanged = pyqtSignal(int)  # user picked a new class for the selected box

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        header = QLabel("Box")
        header.setObjectName("panel-title")
        lay.addWidget(header)

        self.empty_label = QLabel("nothing selected")
        self.empty_label.setObjectName("muted")
        lay.addWidget(self.empty_label)

        self.cls_combo = QComboBox()
        self.cls_combo.setVisible(False)
        self.cls_combo.activated.connect(self.classChanged)
        lay.addWidget(self.cls_combo)

        self.coords_label = QLabel("")
        self.coords_label.setObjectName("mono")
        self.coords_label.setVisible(False)
        self.coords_label.setWordWrap(True)
        lay.addWidget(self.coords_label)

        lay.addStretch(1)

    def set_class_names(self, names: list[str]) -> None:
        current = self.cls_combo.currentIndex()
        self.cls_combo.blockSignals(True)
        self.cls_combo.clear()
        for i, name in enumerate(names):
            pix = QPixmap(12, 12)
            pix.fill(class_color(i))
            self.cls_combo.addItem(QIcon(pix), f"{i} · {name}")
        if 0 <= current < self.cls_combo.count():
            self.cls_combo.setCurrentIndex(current)
        self.cls_combo.blockSignals(False)

    def show_box(self, item: BBoxItem | None) -> None:
        if item is None:
            self.empty_label.setVisible(True)
            self.cls_combo.setVisible(False)
            self.coords_label.setVisible(False)
            return
        self.empty_label.setVisible(False)
        self.cls_combo.setVisible(True)
        self.coords_label.setVisible(True)
        self.cls_combo.blockSignals(True)
        if 0 <= item.class_id < self.cls_combo.count():
            self.cls_combo.setCurrentIndex(item.class_id)
        self.cls_combo.blockSignals(False)
        r = item.absolute_rect()
        self.coords_label.setText(
            f"x  {r.left():.0f}\n"
            f"y  {r.top():.0f}\n"
            f"w  {r.width():.0f}\n"
            f"h  {r.height():.0f}"
        )


class Thumbstrip(QListWidget):
    """Horizontal strip of all workspace images; click to load."""

    selected = pyqtSignal(object)  # Path

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("thumbstrip")
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setFlow(QListWidget.Flow.LeftToRight)
        self.setMovement(QListWidget.Movement.Static)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setWrapping(False)
        self.setIconSize(QSize(THUMB_SIZE, THUMB_SIZE))
        self.setGridSize(QSize(THUMB_SIZE + 12, THUMB_SIZE + 30))
        self.setFixedHeight(THUMB_SIZE + 50)
        self.setSpacing(4)
        self.itemClicked.connect(self._on_clicked)

    def _on_clicked(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(path, Path):
            self.selected.emit(path)


class AnnotationScreen(Screen):
    title = "Annotate"

    def _build(self) -> None:
        self.workspace: Workspace | None = None
        self.current_path: Path | None = None
        self.current_pixmap: QPixmap | None = None
        self.image_w = 0
        self.image_h = 0
        self.pool = QThreadPool.globalInstance()
        self._thumb_cache: dict[Path, QPixmap] = {}
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(300)
        self._save_timer.timeout.connect(self._save_now)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top toolbar ──────────────────────────────────────
        toolbar = QToolBar()
        bar_holder = QWidget()
        bar_lay = QHBoxLayout(bar_holder)
        bar_lay.setContentsMargins(12, 6, 12, 6)
        bar_lay.setSpacing(8)
        self.prev_btn = QPushButton("◀ Prev")
        self.next_btn = QPushButton("Next ▶")
        self.fit_btn = QPushButton("Fit")
        self.title_label = QLabel("no image")
        self.title_label.setObjectName("muted")
        bar_lay.addWidget(self.prev_btn)
        bar_lay.addWidget(self.next_btn)
        bar_lay.addWidget(self.fit_btn)
        bar_lay.addSpacing(16)
        bar_lay.addWidget(self.title_label, 1)
        toolbar.addWidget(bar_holder)
        root.addWidget(toolbar)

        # ── Body: classes | canvas | attrs ───────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)

        self.classes_panel = ClassesPanel()
        self.classes_panel.setFixedWidth(180)
        splitter.addWidget(self.classes_panel)

        self.canvas = AnnotationCanvas()
        splitter.addWidget(self.canvas)

        self.attrs_panel = AttrsPanel()
        self.attrs_panel.setFixedWidth(180)
        splitter.addWidget(self.attrs_panel)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        root.addWidget(splitter, 1)

        # ── Thumbstrip ───────────────────────────────────────
        self.strip = Thumbstrip()
        root.addWidget(self.strip)

        # ── Wire ─────────────────────────────────────────────
        self.prev_btn.clicked.connect(lambda: self._step(-1))
        self.next_btn.clicked.connect(lambda: self._step(1))
        self.fit_btn.clicked.connect(self.canvas.fit_to_view)

        self.classes_panel.activeChanged.connect(self._on_active_class_changed)
        self.classes_panel.classesEdited.connect(self._on_classes_edited)

        scene = self.canvas.canvas_scene
        scene.boxesChanged.connect(self._on_boxes_changed)
        scene.selectionChangedTo.connect(self.attrs_panel.show_box)
        self.canvas.classRequested.connect(self._assign_class_to_selected)
        self.canvas.deleteRequested.connect(self._delete_selected)
        self.attrs_panel.classChanged.connect(self._assign_class_to_selected)
        self.strip.selected.connect(self.load_image)

        self.signals.workspaceOpened.connect(self._on_workspace_opened)
        self.signals.imageSelected.connect(self.load_image)

    # ── Workspace ─────────────────────────────────────────────
    def _on_workspace_opened(self, ws: Workspace) -> None:
        self.workspace = ws
        names = ws.class_names or ["object"]
        self.classes_panel.set_names(names)
        self.attrs_panel.set_class_names(names)
        self.canvas.canvas_scene.active_class_id = self.classes_panel.active_id()
        self._populate_thumbstrip()

    def _populate_thumbstrip(self) -> None:
        self.strip.clear()
        if self.workspace is None:
            return
        for entry in self.workspace.images:
            item = QListWidgetItem(entry.image.name)
            item.setData(Qt.ItemDataRole.UserRole, entry.image)
            placeholder = QPixmap(THUMB_SIZE, THUMB_SIZE)
            placeholder.fill(QColor("#e6e2da"))
            item.setIcon(QIcon(placeholder))
            self.strip.addItem(item)
            self._schedule_thumb(entry.image, item)

    def _schedule_thumb(self, path: Path, item: QListWidgetItem) -> None:
        if path in self._thumb_cache:
            item.setIcon(QIcon(self._thumb_cache[path]))
            return
        task = ThumbnailLoadTask(path, max_side=THUMB_SIZE * 2)
        task.signals.finished.connect(
            lambda p, arr, _it=item: self._on_thumb_ready(p, arr, _it)
        )
        self.pool.start(task)

    def _on_thumb_ready(self, path: Path, arr, item: QListWidgetItem) -> None:
        pix = numpy_to_pixmap(arr)
        scaled = pix.scaled(
            THUMB_SIZE, THUMB_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._thumb_cache[path] = scaled
        try:
            item.setIcon(QIcon(scaled))
        except RuntimeError:
            pass

    # ── Image load + label load ──────────────────────────────
    def load_image(self, path) -> None:
        if not isinstance(path, Path) or self.workspace is None:
            return
        # Flush any pending save for the previous image first.
        if self._save_timer.isActive():
            self._save_timer.stop()
            self._save_now()
        self.current_path = path
        self.title_label.setText(str(path.relative_to(self.workspace.root)) if path.is_relative_to(self.workspace.root) else str(path))
        # Highlight in the strip without firing the click signal again.
        self.strip.blockSignals(True)
        for i in range(self.strip.count()):
            it = self.strip.item(i)
            if it.data(Qt.ItemDataRole.UserRole) == path:
                self.strip.setCurrentItem(it)
                self.strip.scrollToItem(it)
                break
        self.strip.blockSignals(False)

        task = ImageLoadTask(path)
        task.signals.finished.connect(self._on_image_loaded)
        task.signals.failed.connect(lambda p, err: self.signals.status.emit(f"load failed: {err}", "error"))
        self.pool.start(task)

    def _on_image_loaded(self, path: Path, arr) -> None:
        if path != self.current_path:
            return
        pix = numpy_to_pixmap(arr)
        self.current_pixmap = pix
        self.image_w = pix.width()
        self.image_h = pix.height()
        scene = self.canvas.canvas_scene
        scene._suspend_emit = True
        try:
            scene.set_image(pix)
            # Load existing labels.
            entry = next((e for e in self.workspace.images if e.image == path), None)
            if entry and entry.has_label:
                for b in read_labels(entry.label):
                    x1, y1, x2, y2 = b.to_pixel_xyxy(self.image_w, self.image_h)
                    scene.add_box(x1, y1, x2, y2, b.class_id)
        finally:
            scene._suspend_emit = False
        self.canvas.fit_to_view()
        self.canvas.setFocus()

    # ── Editing ───────────────────────────────────────────────
    def _on_active_class_changed(self, idx: int) -> None:
        self.canvas.canvas_scene.active_class_id = idx

    def _on_classes_edited(self, names: list[str]) -> None:
        if self.workspace is None:
            return
        self.attrs_panel.set_class_names(names)
        # Mirror to data.yaml so the next workspace scan picks them up.
        write_data_yaml(self.workspace.data_yaml, names, root=str(self.workspace.root))
        self.workspace.class_names = list(names)

    def _assign_class_to_selected(self, class_id: int) -> None:
        scene = self.canvas.canvas_scene
        changed = False
        for item in scene.selectedItems():
            if isinstance(item, BBoxItem):
                item.set_class(class_id)
                changed = True
        if changed:
            scene._emit_changed()

    def _delete_selected(self) -> None:
        scene = self.canvas.canvas_scene
        removed = False
        for item in list(scene.selectedItems()):
            if isinstance(item, BBoxItem):
                scene.removeItem(item)
                removed = True
        if removed:
            self.attrs_panel.show_box(None)
            scene._emit_changed()

    def _on_boxes_changed(self) -> None:
        # Refresh attrs panel coords live, and arm autosave.
        sel = self.canvas.canvas_scene.selectedItems()
        first = next((i for i in sel if isinstance(i, BBoxItem)), None)
        self.attrs_panel.show_box(first)
        self._save_timer.start()

    def _save_now(self) -> None:
        if self.workspace is None or self.current_path is None:
            return
        if self.image_w <= 0 or self.image_h <= 0:
            return
        # Build YOLO boxes from scene-space coords.
        boxes: list[YoloBox] = []
        for b in self.canvas.canvas_scene.export_boxes():
            boxes.append(
                YoloBox.from_pixel_xyxy(
                    b.class_id, b.x1, b.y1, b.x2, b.y2, self.image_w, self.image_h
                )
            )
        # Target: <workspace>/labels/<stem>.txt (or alongside image if flat layout).
        ws = self.workspace
        label_path = ws.labels_dir / f"{self.current_path.stem}.txt"
        if not ws.labels_dir.exists() and (ws.images_dir == ws.root):
            label_path = self.current_path.with_suffix(".txt")
        task = LabelSaveTask(label_path, boxes)
        task.signals.finished.connect(lambda p: self.signals.annotationsChanged.emit(p))
        task.signals.failed.connect(lambda p, err: self.signals.status.emit(f"save failed: {err}", "error"))
        self.pool.start(task)

    # ── Navigation ────────────────────────────────────────────
    def _step(self, direction: int) -> None:
        if self.workspace is None or self.current_path is None:
            if self.workspace and self.workspace.images:
                self.load_image(self.workspace.images[0].image)
            return
        paths = [e.image for e in self.workspace.images]
        if self.current_path not in paths:
            return
        idx = paths.index(self.current_path)
        nxt = (idx + direction) % len(paths)
        self.load_image(paths[nxt])
