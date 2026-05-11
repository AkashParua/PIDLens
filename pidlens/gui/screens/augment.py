"""Screen 5 — Augmentation (wireframe V3: 3-col card grid).

Each augmentation lives in its own card with an enable toggle, parameters, and
a 4-cell sample grid showing N variations of the same source image under
different RNG draws. The configuration is saved as `augment.yaml` in the
workspace so the Training screen can pick it up.
"""

from __future__ import annotations

import random
from pathlib import Path

import cv2
import numpy as np
import yaml
from PyQt6.QtCore import QSize, Qt, QThreadPool, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from pidlens.core.utils import numpy_to_pixmap
from pidlens.core.workers.io_worker import ThumbnailLoadTask
from pidlens.data.workspace import Workspace
from pidlens.gui.components.widgets import primary_button
from pidlens.gui.screens._base import Screen
from pidlens.ml.vision.augment import AUGS


SAMPLE_PX = 110
N_SAMPLES = 4  # 2×2 grid


class AugCard(QFrame):
    """One augmentation type. Enabled flag, params, 2×2 sample preview."""

    changed = pyqtSignal()

    def __init__(self, aug_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.aug_id = aug_id
        spec = AUGS[aug_id]
        self.setObjectName("aug-card")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 8, 10, 10)
        outer.setSpacing(6)

        head = QHBoxLayout()
        self.enabled = QCheckBox(spec["label"])
        self.enabled.setObjectName("aug-card-title")
        self.enabled.stateChanged.connect(self.changed)
        head.addWidget(self.enabled)
        head.addStretch(1)
        outer.addLayout(head)

        # Params row.
        self.editors: dict[str, QWidget] = {}
        if spec["params"]:
            row = QHBoxLayout()
            row.setSpacing(6)
            for name, default in spec["params"].items():
                lbl = QLabel(name)
                lbl.setObjectName("muted")
                row.addWidget(lbl)
                if isinstance(default, bool):
                    editor = QComboBox()
                    editor.addItems(["false", "true"])
                    editor.setCurrentIndex(1 if default else 0)
                    editor.currentIndexChanged.connect(self.changed)
                elif isinstance(default, int):
                    editor = QSpinBox()
                    editor.setRange(0, 999)
                    editor.setValue(default)
                    editor.valueChanged.connect(self.changed)
                elif isinstance(default, float):
                    editor = QDoubleSpinBox()
                    editor.setRange(0.0, 100.0)
                    editor.setDecimals(2)
                    editor.setSingleStep(0.05)
                    editor.setValue(default)
                    editor.valueChanged.connect(self.changed)
                else:
                    editor = QComboBox()
                    editor.addItem(str(default))
                    editor.currentIndexChanged.connect(self.changed)
                editor.setFixedWidth(72)
                row.addWidget(editor)
                self.editors[name] = editor
            row.addStretch(1)
            outer.addLayout(row)

        # 2×2 sample grid.
        grid_w = QWidget()
        self.grid = QGridLayout(grid_w)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(4)
        self.samples: list[QLabel] = []
        for i in range(N_SAMPLES):
            lbl = QLabel()
            lbl.setFixedSize(SAMPLE_PX, SAMPLE_PX)
            lbl.setObjectName("aug-sample")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFrameShape(QFrame.Shape.StyledPanel)
            lbl.setStyleSheet("background:#ebe8e1;color:#7a7165;")
            self.samples.append(lbl)
            self.grid.addWidget(lbl, i // 2, i % 2)
        outer.addWidget(grid_w)

    # ── State ────────────────────────────────────────────────
    def is_enabled(self) -> bool:
        return self.enabled.isChecked()

    def params(self) -> dict:
        out = {}
        for name, default in AUGS[self.aug_id]["params"].items():
            editor = self.editors[name]
            if isinstance(editor, QSpinBox):
                out[name] = editor.value()
            elif isinstance(editor, QDoubleSpinBox):
                out[name] = editor.value()
            elif isinstance(editor, QComboBox):
                text = editor.currentText()
                out[name] = (text == "true") if isinstance(default, bool) else text
            else:
                out[name] = default
        return out

    def load_state(self, enabled: bool, params: dict) -> None:
        self.enabled.blockSignals(True)
        self.enabled.setChecked(enabled)
        self.enabled.blockSignals(False)
        for name, value in (params or {}).items():
            if name not in self.editors:
                continue
            editor = self.editors[name]
            editor.blockSignals(True)
            if isinstance(editor, (QSpinBox, QDoubleSpinBox)):
                editor.setValue(value)
            elif isinstance(editor, QComboBox):
                idx = editor.findText(str(value).lower() if isinstance(value, bool) else str(value))
                if idx >= 0:
                    editor.setCurrentIndex(idx)
            editor.blockSignals(False)

    def update_samples(self, source: np.ndarray | None, seed: int) -> None:
        if source is None or not self.is_enabled():
            for lbl in self.samples:
                lbl.clear()
            return
        spec = AUGS[self.aug_id]
        fn = spec["fn"]
        merged = {**spec["params"], **self.params()}
        for i, lbl in enumerate(self.samples):
            rng = random.Random(seed + i)
            out = fn(source.copy(), rng, **merged)
            pix = numpy_to_pixmap(out)
            lbl.setPixmap(pix.scaled(
                SAMPLE_PX, SAMPLE_PX,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))


class AugmentScreen(Screen):
    title = "Augment"

    AUGMENT_FILE = "augment.yaml"

    def _build(self) -> None:
        self.workspace: Workspace | None = None
        self.pool = QThreadPool.globalInstance()
        self.cards: dict[str, AugCard] = {}
        self.source_image: np.ndarray | None = None
        self.source_path: Path | None = None
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(120)
        self._refresh_timer.timeout.connect(self._refresh_all_samples)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Toolbar ──────────────────────────────────────────
        toolbar = QToolBar()
        bar_holder = QWidget()
        bar_lay = QHBoxLayout(bar_holder)
        bar_lay.setContentsMargins(12, 6, 12, 6)
        bar_lay.setSpacing(8)

        bar_lay.addWidget(QLabel("Sample image:"))
        self.sample_combo = QComboBox()
        self.sample_combo.setMinimumWidth(220)
        self.sample_combo.currentIndexChanged.connect(self._on_sample_changed)
        bar_lay.addWidget(self.sample_combo)

        bar_lay.addSpacing(12)
        bar_lay.addWidget(QLabel("Seed:"))
        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(0, 2**31 - 1)
        self.seed_spin.setValue(42)
        self.seed_spin.valueChanged.connect(lambda *_: self._schedule_refresh())
        bar_lay.addWidget(self.seed_spin)

        self.reroll_btn = QPushButton("Re-roll")
        self.reroll_btn.clicked.connect(lambda: (self.seed_spin.setValue(random.randint(0, 2**31 - 1))))
        bar_lay.addWidget(self.reroll_btn)

        bar_lay.addStretch(1)

        self.save_btn = primary_button("Save augmentations")
        self.save_btn.clicked.connect(self._on_save)
        bar_lay.addWidget(self.save_btn)
        toolbar.addWidget(bar_holder)
        root.addWidget(toolbar)

        # ── Body: scrollable 3-col grid ──────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(16, 16, 16, 16)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        for i, aug_id in enumerate(AUGS.keys()):
            card = AugCard(aug_id)
            card.changed.connect(self._schedule_refresh)
            self.cards[aug_id] = card
            grid.addWidget(card, i // 3, i % 3)
        # filler row that absorbs trailing space
        grid.setRowStretch(grid.rowCount(), 1)
        scroll.setWidget(container)
        root.addWidget(scroll, 1)

        self.signals.workspaceOpened.connect(self._on_workspace_opened)

    # ── Workspace ────────────────────────────────────────────
    def _on_workspace_opened(self, ws: Workspace) -> None:
        self.workspace = ws
        self.sample_combo.blockSignals(True)
        self.sample_combo.clear()
        for entry in ws.images[:500]:
            self.sample_combo.addItem(entry.image.name, entry.image)
        self.sample_combo.blockSignals(False)
        self._load_config()
        if self.sample_combo.count():
            self.sample_combo.setCurrentIndex(0)

    def _on_sample_changed(self, _idx: int) -> None:
        path = self.sample_combo.currentData()
        if not isinstance(path, Path):
            return
        self.source_path = path
        task = ThumbnailLoadTask(path, max_side=SAMPLE_PX * 2)
        task.signals.finished.connect(self._on_source_loaded)
        self.pool.start(task)

    def _on_source_loaded(self, path: Path, arr: np.ndarray) -> None:
        if path != self.source_path:
            return
        self.source_image = arr
        self._refresh_all_samples()

    # ── Refresh ──────────────────────────────────────────────
    def _schedule_refresh(self) -> None:
        self._refresh_timer.start()

    def _refresh_all_samples(self) -> None:
        seed = self.seed_spin.value()
        for card in self.cards.values():
            card.update_samples(self.source_image, seed)

    # ── Save/load augment.yaml ───────────────────────────────
    def _config(self) -> dict:
        return {
            "seed": self.seed_spin.value(),
            "augmentations": [
                {"id": aug_id, "enabled": c.is_enabled(), "params": c.params()}
                for aug_id, c in self.cards.items()
            ],
        }

    def _on_save(self) -> None:
        if self.workspace is None:
            return
        path = self.workspace.root / self.AUGMENT_FILE
        path.write_text(yaml.safe_dump(self._config(), sort_keys=False), encoding="utf-8")
        self.signals.status.emit(f"saved {path.name}", "info")

    def _load_config(self) -> None:
        if self.workspace is None:
            return
        path = self.workspace.root / self.AUGMENT_FILE
        if not path.exists():
            return
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            return
        if "seed" in data:
            self.seed_spin.blockSignals(True)
            self.seed_spin.setValue(int(data["seed"]))
            self.seed_spin.blockSignals(False)
        for entry in data.get("augmentations") or []:
            card = self.cards.get(entry.get("id"))
            if card:
                card.load_state(bool(entry.get("enabled")), entry.get("params") or {})
