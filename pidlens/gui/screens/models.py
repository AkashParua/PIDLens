"""Screen 8 — Model registry / eval (wireframe V1: runs table + detail panel)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pidlens.data.runs import RunRecord, list_runs, register_model
from pidlens.data.workspace import Workspace
from pidlens.gui.components.charts import Sparkline
from pidlens.gui.components.widgets import StatBlock, primary_button
from pidlens.gui.screens._base import Screen


class ModelsScreen(Screen):
    title = "Models"

    def _build(self) -> None:
        self.workspace: Workspace | None = None
        self.runs: list[RunRecord] = []
        self.selected: RunRecord | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header bar
        header = QHBoxLayout()
        header.setContentsMargins(16, 12, 16, 0)
        title = QLabel("Runs")
        title.setObjectName("screen-title")
        header.addWidget(title)
        header.addStretch(1)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh)
        header.addWidget(self.refresh_btn)
        root.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)

        # ── Runs table ───────────────────────────────────────
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["run", "epochs", "best mAP50", "final loss", "weights", "registered"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c in range(1, 6):
            h.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._on_row_changed)
        splitter.addWidget(self.table)

        # ── Detail panel ─────────────────────────────────────
        detail = QWidget()
        detail_lay = QVBoxLayout(detail)
        detail_lay.setContentsMargins(12, 12, 12, 12)
        detail_lay.setSpacing(10)

        self.run_title = QLabel("nothing selected")
        self.run_title.setObjectName("panel-title")
        detail_lay.addWidget(self.run_title)

        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(6)
        self.kpi_epochs = StatBlock("epochs", "—", "")
        self.kpi_best = StatBlock("best mAP50", "—", "")
        self.kpi_loss = StatBlock("final loss", "—", "")
        for s in (self.kpi_epochs, self.kpi_best, self.kpi_loss):
            kpi_row.addWidget(s, 1)
        detail_lay.addLayout(kpi_row)

        self.loss_chart = Sparkline()
        self.loss_chart.set_series("loss", [], QColor("#c96442"))
        self.map_chart = Sparkline()
        self.map_chart.set_series("mAP50", [], QColor("#3a8a4a"))
        detail_lay.addWidget(self.loss_chart)
        detail_lay.addWidget(self.map_chart)

        btn_row = QHBoxLayout()
        self.register_btn = primary_button("Register as model")
        self.register_btn.setEnabled(False)
        self.register_btn.clicked.connect(self._on_register)
        btn_row.addWidget(self.register_btn)
        btn_row.addStretch(1)
        detail_lay.addLayout(btn_row)

        detail_lay.addStretch(1)
        splitter.addWidget(detail)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([700, 400])
        root.addWidget(splitter, 1)

        self.signals.workspaceOpened.connect(self._on_workspace_opened)
        self.signals.trainingFinished.connect(lambda *_: self._refresh())

    def _on_workspace_opened(self, ws: Workspace) -> None:
        self.workspace = ws
        self._refresh()

    def _refresh(self) -> None:
        if self.workspace is None:
            return
        self.runs = list_runs(self.workspace)
        self.table.setRowCount(0)
        for run in self.runs:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(run.run_id))
            epochs = run.summary.get("epochs_completed") or run.config.get("epochs") or "—"
            self.table.setItem(row, 1, QTableWidgetItem(str(epochs)))
            best = run.summary.get("best") or {}
            best_map = best.get("mAP50")
            self.table.setItem(row, 2, QTableWidgetItem(f"{best_map:.3f}" if isinstance(best_map, (int, float)) else "—"))
            final = run.summary.get("final") or {}
            final_loss = final.get("loss")
            self.table.setItem(row, 3, QTableWidgetItem(f"{final_loss:.3f}" if isinstance(final_loss, (int, float)) else "—"))
            self.table.setItem(row, 4, QTableWidgetItem("yes" if run.weights else "no"))
            registered = (self.workspace.models_dir / f"{run.run_id}.pt").exists()
            self.table.setItem(row, 5, QTableWidgetItem("yes" if registered else "—"))
        if self.runs:
            self.table.selectRow(0)

    def _on_row_changed(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            self.selected = None
            self.run_title.setText("nothing selected")
            self.register_btn.setEnabled(False)
            return
        row = rows[0].row()
        if row < 0 or row >= len(self.runs):
            return
        run = self.runs[row]
        self.selected = run
        self.run_title.setText(run.run_id)
        epochs = run.summary.get("epochs_completed") or len(run.history)
        self.kpi_epochs.set_value(str(epochs))
        best = run.summary.get("best") or {}
        final = run.summary.get("final") or {}
        self.kpi_best.set_value(
            f"{best.get('mAP50', 0):.3f}" if "mAP50" in best else "—"
        )
        self.kpi_loss.set_value(
            f"{final.get('loss', 0):.3f}" if "loss" in final else "—"
        )
        losses = [h.get("loss", 0.0) for h in run.history]
        maps = [h.get("mAP50", 0.0) for h in run.history]
        self.loss_chart.set_series("loss", losses, QColor("#c96442"))
        self.map_chart.set_series("mAP50", maps, QColor("#3a8a4a"))
        self.register_btn.setEnabled(run.weights is not None)

    def _on_register(self) -> None:
        if self.selected is None or self.workspace is None:
            return
        alias, ok = QInputDialog.getText(
            self, "Register model", "Alias:", text=self.selected.run_id
        )
        if not ok or not alias.strip():
            return
        try:
            target = register_model(self.workspace, self.selected, alias.strip())
        except FileNotFoundError as e:
            QMessageBox.warning(self, "No weights", str(e))
            return
        self.signals.status.emit(f"registered → {target.name}", "info")
        self._refresh()
