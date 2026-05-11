"""Screen 6 — Train / val / test split (wireframe V3: donut + per-class bars)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from pidlens.config import (
    WORKSPACE_IMAGES_DIR,
    WORKSPACE_LABELS_DIR,
)
from pidlens.data.split import compute_split, write_split_lists
from pidlens.data.workspace import Workspace
from pidlens.data.yolo_parser import write_data_yaml
from pidlens.gui.components.charts import DonutChart, StackedClassBars
from pidlens.gui.components.widgets import StatBlock, primary_button
from pidlens.gui.screens._base import Screen


class SplitScreen(Screen):
    title = "Split"

    def _build(self) -> None:
        self.workspace: Workspace | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Toolbar with split ratios ────────────────────────
        toolbar = QToolBar()
        bar_holder = QWidget()
        bar_lay = QHBoxLayout(bar_holder)
        bar_lay.setContentsMargins(12, 6, 12, 6)
        bar_lay.setSpacing(8)

        bar_lay.addWidget(QLabel("Train"))
        self.train_spin = QDoubleSpinBox()
        self.train_spin.setRange(0.0, 1.0)
        self.train_spin.setSingleStep(0.05)
        self.train_spin.setDecimals(2)
        self.train_spin.setValue(0.70)
        bar_lay.addWidget(self.train_spin)

        bar_lay.addWidget(QLabel("Val"))
        self.val_spin = QDoubleSpinBox()
        self.val_spin.setRange(0.0, 1.0)
        self.val_spin.setSingleStep(0.05)
        self.val_spin.setDecimals(2)
        self.val_spin.setValue(0.15)
        bar_lay.addWidget(self.val_spin)

        bar_lay.addWidget(QLabel("Test"))
        self.test_spin = QDoubleSpinBox()
        self.test_spin.setRange(0.0, 1.0)
        self.test_spin.setSingleStep(0.05)
        self.test_spin.setDecimals(2)
        self.test_spin.setValue(0.15)
        bar_lay.addWidget(self.test_spin)

        bar_lay.addSpacing(8)
        self.strat_box = QCheckBox("stratified")
        self.strat_box.setChecked(True)
        bar_lay.addWidget(self.strat_box)

        bar_lay.addSpacing(8)
        bar_lay.addWidget(QLabel("Seed"))
        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(0, 2**31 - 1)
        self.seed_spin.setValue(42)
        bar_lay.addWidget(self.seed_spin)

        bar_lay.addStretch(1)

        self.preview_btn = QLabelButton("Preview")
        self.preview_btn.clicked.connect(self._compute)
        bar_lay.addWidget(self.preview_btn)

        self.write_btn = primary_button("Write train/val/test")
        self.write_btn.clicked.connect(self._write_split)
        bar_lay.addWidget(self.write_btn)

        toolbar.addWidget(bar_holder)
        root.addWidget(toolbar)

        # ── Body ─────────────────────────────────────────────
        body = QHBoxLayout()
        body.setContentsMargins(16, 16, 16, 16)
        body.setSpacing(16)

        # Left: donut + summary stat blocks below.
        left_col = QVBoxLayout()
        left_col.setSpacing(12)
        self.donut = DonutChart()
        left_col.addWidget(self.donut, 1)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(6)
        self.stat_train = StatBlock("train", "—", "")
        self.stat_val = StatBlock("val", "—", "")
        self.stat_test = StatBlock("test", "—", "")
        self.stat_unlabeled = StatBlock("unlabeled", "—", "excluded")
        for s in (self.stat_train, self.stat_val, self.stat_test, self.stat_unlabeled):
            stats_row.addWidget(s, 1)
        left_col.addLayout(stats_row)
        body.addLayout(left_col, 1)

        # Right: per-class bars.
        right_col = QVBoxLayout()
        right_col.setSpacing(8)
        right_col.addWidget(QLabel("Per-class box counts"))
        self.bars = StackedClassBars()
        right_col.addWidget(self.bars, 1)
        body.addLayout(right_col, 1)

        root.addLayout(body, 1)

        # Wire
        for w in (self.train_spin, self.val_spin, self.test_spin, self.seed_spin):
            w.valueChanged.connect(self._compute)
        self.strat_box.stateChanged.connect(self._compute)
        self.signals.workspaceOpened.connect(self._on_workspace_opened)

    def _on_workspace_opened(self, ws: Workspace) -> None:
        self.workspace = ws
        self._compute()

    def _compute(self) -> None:
        if self.workspace is None:
            return
        split = compute_split(
            self.workspace,
            train=self.train_spin.value(),
            val=self.val_spin.value(),
            test=self.test_spin.value(),
            stratified=self.strat_box.isChecked(),
            seed=self.seed_spin.value(),
        )
        self._last = split
        self.donut.set_counts(len(split.train), len(split.val), len(split.test))
        self.stat_train.set_value(str(len(split.train)))
        self.stat_val.set_value(str(len(split.val)))
        self.stat_test.set_value(str(len(split.test)))
        self.stat_unlabeled.set_value(str(len(split.unlabeled)))

        names = self.workspace.class_names
        rows: list[tuple[str, tuple[int, int, int]]] = []
        for cid in sorted(split.per_class_boxes.keys()):
            label = names[cid] if 0 <= cid < len(names) else f"#{cid}"
            rows.append((label, split.per_class_boxes[cid]))
        self.bars.set_rows(rows)

    def _write_split(self) -> None:
        if self.workspace is None or not hasattr(self, "_last"):
            self._compute()
        ws = self.workspace
        if ws is None:
            return
        paths = write_split_lists(ws, self._last)
        # Also update data.yaml to point at the split lists.
        write_data_yaml(
            ws.data_yaml,
            ws.class_names or ["object"],
            root=str(ws.root),
            train=str(paths["train"].name),
            val=str(paths["val"].name),
            test=str(paths["test"].name),
        )
        self.signals.status.emit(
            f"wrote train/val/test ({len(self._last.train)}/{len(self._last.val)}/{len(self._last.test)})",
            "info",
        )


# A tiny helper — non-primary button with the same construction as primary_button.
def QLabelButton(text: str):
    from PyQt6.QtWidgets import QPushButton
    return QPushButton(text)
