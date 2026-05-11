"""Screen 4 — Preprocessing pipeline (wireframe V3: in/out preview per card).

Left: scrollable column of "op cards", each card a single transformation with
its own params + per-card in/out thumbs. Right: full-size before/after of the
selected workspace image. Top toolbar: pick the source version (raw, v1, v2…),
add ops, and apply-to-all to write a new version directory.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QThreadPool, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from pidlens.core.utils import numpy_to_pixmap
from pidlens.core.workers.io_worker import ImageLoadTask
from pidlens.core.workers.vision_worker import BatchPreprocessTask, VisionPipelineTask
from pidlens.data.workspace import Workspace
from pidlens.data.yaml_manager import list_versions, next_version_dir
from pidlens.gui.components.widgets import primary_button
from pidlens.gui.screens._base import Screen
from pidlens.ml.vision.morphology import OPS


PREVIEW_THUMB = QSize(220, 130)


class OpCard(QFrame):
    """One step in the pipeline. Editable params, scope, removable."""

    changed = pyqtSignal()
    removeRequested = pyqtSignal(object)  # self

    def __init__(self, op_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("op-card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.op_id = op_id
        spec = OPS[op_id]

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 8, 10, 10)
        outer.setSpacing(6)

        # ── Header: title + scope + remove ───────────────────
        head = QHBoxLayout()
        title = QLabel(spec["label"])
        title.setObjectName("op-card-title")
        head.addWidget(title)
        head.addStretch(1)
        self.scope_combo = QComboBox()
        for s in spec["scopes"]:
            self.scope_combo.addItem(s)
        self.scope_combo.currentIndexChanged.connect(self.changed)
        head.addWidget(self.scope_combo)
        rm = QPushButton("✕")
        rm.setFixedWidth(24)
        rm.setFlat(True)
        rm.clicked.connect(lambda: self.removeRequested.emit(self))
        head.addWidget(rm)
        outer.addLayout(head)

        # ── Params row ───────────────────────────────────────
        self.param_editors: dict[str, QWidget] = {}
        if spec["params"]:
            params_row = QHBoxLayout()
            params_row.setSpacing(6)
            for name, default in spec["params"].items():
                label = QLabel(name)
                label.setObjectName("muted")
                params_row.addWidget(label)
                if isinstance(default, bool):
                    editor = QComboBox()
                    editor.addItems(["false", "true"])
                    editor.setCurrentIndex(1 if default else 0)
                    editor.currentIndexChanged.connect(self.changed)
                elif isinstance(default, int):
                    editor = QSpinBox()
                    editor.setRange(0, 9999)
                    editor.setValue(default)
                    editor.valueChanged.connect(self.changed)
                elif isinstance(default, float):
                    editor = QDoubleSpinBox()
                    editor.setRange(0.0, 100.0)
                    editor.setDecimals(2)
                    editor.setSingleStep(0.1)
                    editor.setValue(default)
                    editor.valueChanged.connect(self.changed)
                else:
                    editor = QComboBox()
                    if name == "method":
                        editor.addItems(["otsu", "adaptive", "fixed"])
                        idx = editor.findText(str(default))
                        if idx >= 0:
                            editor.setCurrentIndex(idx)
                    else:
                        editor.addItem(str(default))
                    editor.currentIndexChanged.connect(self.changed)
                editor.setFixedWidth(80)
                params_row.addWidget(editor)
                self.param_editors[name] = editor
            params_row.addStretch(1)
            outer.addLayout(params_row)

        # ── In/Out preview thumbs ────────────────────────────
        previews = QHBoxLayout()
        previews.setSpacing(8)
        self.thumb_in = QLabel("in")
        self.thumb_out = QLabel("out")
        for lbl in (self.thumb_in, self.thumb_out):
            lbl.setFixedSize(PREVIEW_THUMB)
            lbl.setObjectName("op-thumb")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFrameShape(QFrame.Shape.StyledPanel)
            lbl.setStyleSheet("background:#ebe8e1;color:#7a7165;")
        previews.addWidget(self.thumb_in)
        previews.addWidget(self.thumb_out)
        previews.addStretch(1)
        outer.addLayout(previews)

    def scope(self) -> str:
        return self.scope_combo.currentText()

    def params(self) -> dict:
        out = {}
        spec_params = OPS[self.op_id]["params"]
        for name, default in spec_params.items():
            editor = self.param_editors[name]
            if isinstance(editor, QSpinBox):
                out[name] = editor.value()
            elif isinstance(editor, QDoubleSpinBox):
                out[name] = editor.value()
            elif isinstance(editor, QComboBox):
                text = editor.currentText()
                if isinstance(default, bool):
                    out[name] = text == "true"
                else:
                    out[name] = text
            else:
                out[name] = default
        return out

    def set_in_pixmap(self, pix: QPixmap | None) -> None:
        if pix is None:
            self.thumb_in.setText("in")
            self.thumb_in.setPixmap(QPixmap())
        else:
            self.thumb_in.setPixmap(pix.scaled(
                PREVIEW_THUMB, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))

    def set_out_pixmap(self, pix: QPixmap | None) -> None:
        if pix is None:
            self.thumb_out.setText("out")
            self.thumb_out.setPixmap(QPixmap())
        else:
            self.thumb_out.setPixmap(pix.scaled(
                PREVIEW_THUMB, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))


class PreprocessScreen(Screen):
    title = "Preprocess"

    def _build(self) -> None:
        self.workspace: Workspace | None = None
        self.pool = QThreadPool.globalInstance()
        self.cards: list[OpCard] = []
        self.preview_path: Path | None = None
        self._preview_input: QPixmap | None = None
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(200)
        self._preview_timer.timeout.connect(self._rerun_preview)
        self._batch_task: BatchPreprocessTask | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Toolbar ──────────────────────────────────────────
        toolbar = QToolBar()
        bar_holder = QWidget()
        bar_lay = QHBoxLayout(bar_holder)
        bar_lay.setContentsMargins(12, 6, 12, 6)
        bar_lay.setSpacing(8)

        bar_lay.addWidget(QLabel("Source:"))
        self.source_combo = QComboBox()
        self.source_combo.setMinimumWidth(140)
        bar_lay.addWidget(self.source_combo)

        bar_lay.addSpacing(12)
        bar_lay.addWidget(QLabel("Add op:"))
        self.op_combo = QComboBox()
        for op_id, spec in OPS.items():
            self.op_combo.addItem(spec["label"], op_id)
        bar_lay.addWidget(self.op_combo)
        self.add_op_btn = QPushButton("+ Add")
        self.add_op_btn.clicked.connect(self._on_add_op)
        bar_lay.addWidget(self.add_op_btn)

        bar_lay.addStretch(1)

        self.apply_btn = primary_button("Apply to all → new version")
        self.apply_btn.clicked.connect(self._on_apply_all)
        bar_lay.addWidget(self.apply_btn)
        toolbar.addWidget(bar_holder)
        root.addWidget(toolbar)

        # ── Body: pipeline | preview ─────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)

        # Left: scrollable pipeline.
        left_holder = QWidget()
        left_outer = QVBoxLayout(left_holder)
        left_outer.setContentsMargins(0, 0, 0, 0)
        left_outer.setSpacing(0)
        left_label = QLabel("Pipeline")
        left_label.setObjectName("section-head")
        left_label.setContentsMargins(12, 8, 12, 8)
        left_outer.addWidget(left_label)

        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(10, 10, 10, 10)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch(1)
        self.cards_scroll.setWidget(self.cards_container)
        left_outer.addWidget(self.cards_scroll, 1)
        splitter.addWidget(left_holder)

        # Right: full preview.
        right_holder = QWidget()
        right_outer = QVBoxLayout(right_holder)
        right_outer.setContentsMargins(0, 0, 0, 0)
        right_outer.setSpacing(0)

        right_top = QHBoxLayout()
        right_top.setContentsMargins(12, 8, 12, 8)
        right_top.setSpacing(8)
        right_top.addWidget(QLabel("Preview:"))
        self.preview_combo = QComboBox()
        self.preview_combo.setMinimumWidth(280)
        self.preview_combo.currentIndexChanged.connect(self._on_preview_changed)
        right_top.addWidget(self.preview_combo, 1)
        right_outer.addLayout(right_top)

        preview_row = QHBoxLayout()
        preview_row.setContentsMargins(12, 0, 12, 12)
        preview_row.setSpacing(8)
        self.preview_in = QLabel("input")
        self.preview_out = QLabel("output")
        for lbl in (self.preview_in, self.preview_out):
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFrameShape(QFrame.Shape.StyledPanel)
            lbl.setStyleSheet("background:#ebe8e1;color:#7a7165;")
            lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            lbl.setMinimumSize(300, 240)
        preview_row.addWidget(self.preview_in, 1)
        preview_row.addWidget(self.preview_out, 1)
        right_outer.addLayout(preview_row, 1)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        right_outer.addWidget(self.progress)

        splitter.addWidget(right_holder)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([460, 900])
        root.addWidget(splitter, 1)

        # Wire
        self.source_combo.currentIndexChanged.connect(self._on_source_changed)
        self.signals.workspaceOpened.connect(self._on_workspace_opened)

    # ── Workspace ────────────────────────────────────────────
    def _on_workspace_opened(self, ws: Workspace) -> None:
        self.workspace = ws
        self._refresh_sources()
        self._populate_preview_combo()

    def _refresh_sources(self) -> None:
        if self.workspace is None:
            return
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("raw (originals)", None)
        for v in list_versions(self.workspace.preprocess_dir):
            self.source_combo.addItem(v.name, v)
        self.source_combo.blockSignals(False)

    def _populate_preview_combo(self) -> None:
        if self.workspace is None:
            return
        self.preview_combo.blockSignals(True)
        self.preview_combo.clear()
        for entry in self.workspace.images[:500]:
            self.preview_combo.addItem(entry.image.name, entry.image)
        self.preview_combo.blockSignals(False)
        if self.preview_combo.count():
            self.preview_combo.setCurrentIndex(0)
            self._on_preview_changed(0)

    def _on_source_changed(self, _idx: int) -> None:
        self._populate_preview_combo()

    # ── Op cards ─────────────────────────────────────────────
    def _on_add_op(self) -> None:
        op_id = self.op_combo.currentData()
        if not op_id:
            return
        self._add_card(op_id)

    def _add_card(self, op_id: str) -> None:
        card = OpCard(op_id)
        card.changed.connect(self._schedule_preview)
        card.removeRequested.connect(self._remove_card)
        # Insert before the trailing stretch.
        self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
        self.cards.append(card)
        self._schedule_preview()

    def _remove_card(self, card: OpCard) -> None:
        if card in self.cards:
            self.cards.remove(card)
        card.setParent(None)
        card.deleteLater()
        self._schedule_preview()

    def _ops_spec(self) -> list[tuple[str, str, dict]]:
        return [(c.op_id, c.scope(), c.params()) for c in self.cards]

    # ── Preview pipeline ─────────────────────────────────────
    def _on_preview_changed(self, _idx: int) -> None:
        path = self.preview_combo.currentData()
        if not isinstance(path, Path):
            self.preview_path = None
            return
        self.preview_path = path
        task = ImageLoadTask(path)
        task.signals.finished.connect(self._on_preview_loaded)
        self.pool.start(task)

    def _on_preview_loaded(self, path: Path, arr) -> None:
        if path != self.preview_path:
            return
        pix = numpy_to_pixmap(arr)
        self._preview_input = pix
        self._set_preview_label(self.preview_in, pix)
        # Also seed each op card's "in" thumb with the original; the chain
        # output gets filled in by _rerun_preview.
        for card in self.cards:
            card.set_in_pixmap(pix)
        self._rerun_preview()

    def _schedule_preview(self) -> None:
        self._preview_timer.start()

    def _rerun_preview(self) -> None:
        if self.preview_path is None or self._preview_input is None or not self.cards:
            self._set_preview_label(self.preview_out, self._preview_input)
            for card in self.cards:
                card.set_out_pixmap(None)
            return
        # Run the full chain on the preview image. Intermediate results feed
        # both each card's `out` thumb and the next card's `in` thumb.
        task = VisionPipelineTask(self.preview_path, self._ops_spec())
        # We want per-step output too — VisionPipelineTask only emits final;
        # for now show original in / final out at full size, and let each
        # card's thumbnails approximate via the inputs alone.
        task.signals.finished.connect(self._on_preview_chain_done)
        self.pool.start(task)

    def _on_preview_chain_done(self, path: Path, arr) -> None:
        if path != self.preview_path:
            return
        pix = numpy_to_pixmap(arr)
        self._set_preview_label(self.preview_out, pix)
        # Final op card shows the final output as its 'out' for quick scan.
        if self.cards:
            self.cards[-1].set_out_pixmap(pix)

    def _set_preview_label(self, lbl: QLabel, pix: QPixmap | None) -> None:
        if pix is None:
            lbl.setPixmap(QPixmap())
            return
        lbl.setPixmap(pix.scaled(
            lbl.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))

    # ── Apply to all → new version ───────────────────────────
    def _on_apply_all(self) -> None:
        if self.workspace is None or not self.cards:
            return
        parent_idx = self.source_combo.currentIndex()
        parent_dir = self.source_combo.itemData(parent_idx)  # Path or None
        # Source entries: raw or a prior version's images.
        if parent_dir is None:
            entries = list(self.workspace.images)
            parent_name = None
        else:
            # Build ImageEntry list from the version's own images/ + labels/.
            from pidlens.data.workspace import ImageEntry
            from pidlens.config import IMAGE_EXTS
            imgs = sorted(
                p for p in (parent_dir / "images").iterdir()
                if p.suffix.lower() in IMAGE_EXTS
            )
            entries = []
            for p in imgs:
                lbl = parent_dir / "labels" / f"{p.stem}.txt"
                entries.append(ImageEntry(image=p, label=lbl if lbl.exists() else None))
            parent_name = parent_dir.name

        if not entries:
            QMessageBox.information(self, "No source", "No images to process.")
            return

        version_dir = next_version_dir(self.workspace.preprocess_dir)
        self.progress.setVisible(True)
        self.progress.setRange(0, len(entries))
        self.progress.setValue(0)
        self.apply_btn.setEnabled(False)

        task = BatchPreprocessTask(entries, self._ops_spec(), version_dir, parent_version=parent_name)
        task.signals.progress.connect(self._on_batch_progress)
        task.signals.finished.connect(self._on_batch_finished)
        task.signals.failed.connect(self._on_batch_failed)
        self._batch_task = task
        self.pool.start(task)

    def _on_batch_progress(self, _vdir: Path, done: int, total: int) -> None:
        self.progress.setMaximum(total)
        self.progress.setValue(done)

    def _on_batch_finished(self, version_dir: Path) -> None:
        self.progress.setVisible(False)
        self.apply_btn.setEnabled(True)
        self._batch_task = None
        self.signals.preprocessVersionCreated.emit(version_dir)
        self.signals.status.emit(f"wrote {version_dir.name}", "info")
        self._refresh_sources()

    def _on_batch_failed(self, version_dir: Path, err: str) -> None:
        self.progress.setVisible(False)
        self.apply_btn.setEnabled(True)
        self._batch_task = None
        QMessageBox.critical(self, "Preprocess failed", err)
