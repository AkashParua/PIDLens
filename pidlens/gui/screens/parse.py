"""Screen 1 — Parse landing (wireframe V2: file tree + parse preview)."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QDir, Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

# QFileSystemModel moved between PyQt6 versions (6.0–6.4: QtWidgets; 6.5+:
# QtGui). Try both so users on either side work without editing imports.
try:
    from PyQt6.QtGui import QFileSystemModel
except ImportError:
    from PyQt6.QtWidgets import QFileSystemModel

from pidlens.config import IMAGE_EXTS
from pidlens.data.workspace import Workspace
from pidlens.gui.components.widgets import StatBlock, primary_button
from pidlens.gui.screens._base import Screen


class ParseScreen(Screen):
    title = "Parse"

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Toolbar ──────────────────────────────────────────
        toolbar = QToolBar()
        toolbar.setObjectName("parse-toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(toolbar.iconSize())

        self.up_btn = QPushButton("↑ Up")
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("/path/to/dataset")
        self.refresh_btn = QPushButton("Refresh")
        self.parse_btn = primary_button("Parse")
        self.parse_btn.setEnabled(False)

        bar_holder = QWidget()
        bar_lay = QHBoxLayout(bar_holder)
        bar_lay.setContentsMargins(12, 8, 12, 8)
        bar_lay.setSpacing(8)
        bar_lay.addWidget(self.up_btn)
        bar_lay.addWidget(self.path_edit, 1)
        bar_lay.addWidget(self.refresh_btn)
        bar_lay.addWidget(self.parse_btn)
        toolbar.addWidget(bar_holder)
        root.addWidget(toolbar)

        # ── Body: tree | (stats / preview) ───────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)
        root.addWidget(splitter, 1)

        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath(QDir.rootPath())
        self.fs_model.setFilter(QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot)

        self.tree = QTreeView()
        self.tree.setModel(self.fs_model)
        self.tree.setColumnHidden(1, True)  # size
        self.tree.setColumnHidden(2, True)  # type
        self.tree.setColumnHidden(3, True)  # date
        self.tree.setHeaderHidden(True)
        self.tree.setMinimumWidth(220)
        self.tree.setRootIsDecorated(True)
        splitter.addWidget(self.tree)

        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(12, 12, 12, 12)
        right_lay.setSpacing(12)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([260, 900])

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(8)
        self.stat_images = StatBlock("images", "—", ".jpg .png")
        self.stat_labeled = StatBlock("with labels", "—", "—")
        self.stat_unlabeled = StatBlock("un-annotated", "—", "needs work")
        self.stat_classes = StatBlock("classes detected", "—", "data.yaml")
        self.stat_orphans = StatBlock("orphan labels", "—", "missing img")
        for w in (
            self.stat_images,
            self.stat_labeled,
            self.stat_unlabeled,
            self.stat_classes,
            self.stat_orphans,
        ):
            stats_row.addWidget(w, 1)
        right_lay.addLayout(stats_row)

        # Preview table
        self.preview_header = QLabel("Parse preview")
        self.preview_header.setObjectName("section-head")
        right_lay.addWidget(self.preview_header)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["file", "size", "status", "classes"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        right_lay.addWidget(self.table, 1)

        # ── Wire ──────────────────────────────────────────────
        self.up_btn.clicked.connect(self._go_up)
        self.refresh_btn.clicked.connect(self._refresh_count)
        self.parse_btn.clicked.connect(self._do_parse)
        self.path_edit.returnPressed.connect(self._set_path_from_edit)
        self.tree.clicked.connect(self._on_tree_click)
        self.signals.workspaceOpened.connect(self._on_workspace_opened)

        # Start at $HOME
        self._set_root(Path.home())

    # ── helpers ──────────────────────────────────────────────
    def _set_root(self, path: Path) -> None:
        path = path.expanduser().resolve()
        if not path.exists():
            return
        self.path_edit.setText(str(path))
        idx = self.fs_model.setRootPath(str(path.parent))
        self.tree.setRootIndex(self.fs_model.index(str(path.parent)))
        focus = self.fs_model.index(str(path))
        if focus.isValid():
            self.tree.setCurrentIndex(focus)
            self.tree.expand(focus)
            self.tree.scrollTo(focus)
        self._refresh_count()

    def _current_path(self) -> Path:
        text = self.path_edit.text().strip()
        return Path(text).expanduser() if text else Path.home()

    def _go_up(self) -> None:
        p = self._current_path()
        if p.parent and p.parent != p:
            self._set_root(p.parent)

    def _set_path_from_edit(self) -> None:
        self._set_root(self._current_path())

    def _on_tree_click(self, idx) -> None:
        path = Path(self.fs_model.filePath(idx))
        if path.is_dir():
            self.path_edit.setText(str(path))
            self._refresh_count()

    def _count_images(self, root: Path) -> int:
        if not root.exists() or not root.is_dir():
            return 0
        n = 0
        # Cap depth and width — counting 100k+ files would jank the UI.
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
                n += 1
                if n > 5000:
                    break
        return n

    def _refresh_count(self) -> None:
        n = self._count_images(self._current_path())
        if n == 0:
            self.parse_btn.setText("Parse")
            self.parse_btn.setEnabled(False)
        else:
            suffix = "+" if n >= 5000 else ""
            self.parse_btn.setText(f"Parse · {n}{suffix} files")
            self.parse_btn.setEnabled(True)

    def _do_parse(self) -> None:
        path = self._current_path()
        if not path.is_dir():
            return
        ws = Workspace(path)
        ws.scan()
        self.signals.workspaceOpened.emit(ws)

    # ── reacts to workspace ──────────────────────────────────
    def _on_workspace_opened(self, ws: Workspace) -> None:
        self.path_edit.setText(str(ws.root))
        self.stat_images.set_value(str(ws.total))
        self.stat_labeled.set_value(str(ws.annotated))
        self.stat_labeled.set_sub(
            f"{(ws.annotated / ws.total * 100):.1f}%" if ws.total else "—"
        )
        self.stat_unlabeled.set_value(str(ws.unannotated))
        self.stat_classes.set_value(str(len(ws.class_names)) if ws.class_names else "0")
        self.stat_classes.set_sub(
            ", ".join(ws.class_names[:3]) + ("…" if len(ws.class_names) > 3 else "")
            if ws.class_names
            else "no data.yaml"
        )
        self.stat_orphans.set_value(str(len(ws.orphan_labels)))

        self._populate_preview(ws)

    def _populate_preview(self, ws: Workspace) -> None:
        self.table.setRowCount(0)
        # Show first 200 to keep UI responsive; Triage handles the full set.
        from pidlens.data.yolo_parser import read_labels

        for entry in ws.images[:200]:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(entry.image.name))
            try:
                size_bytes = entry.image.stat().st_size
                size = f"{size_bytes / 1024:.0f} KB" if size_bytes < 1_048_576 else f"{size_bytes / 1_048_576:.1f} MB"
            except OSError:
                size = "—"
            self.table.setItem(row, 1, QTableWidgetItem(size))

            if entry.has_label:
                boxes = read_labels(entry.label) if entry.label else []
                cls_ids = sorted({b.class_id for b in boxes})
                names = []
                for cid in cls_ids:
                    if 0 <= cid < len(ws.class_names):
                        names.append(ws.class_names[cid])
                    else:
                        names.append(f"#{cid}")
                self.table.setItem(row, 2, QTableWidgetItem(f"✓ {len(boxes)} box{'es' if len(boxes) != 1 else ''}"))
                self.table.setItem(row, 3, QTableWidgetItem(", ".join(names) if names else "—"))
            else:
                self.table.setItem(row, 2, QTableWidgetItem("— no labels"))
                self.table.setItem(row, 3, QTableWidgetItem("—"))

        self.preview_header.setText(
            f"Parse preview — showing {min(len(ws.images), 200)} of {len(ws.images)}"
        )
