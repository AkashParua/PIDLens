"""Screen 7 — Training loop (wireframe V2: KPIs · 2 charts · terminal).

Top: KPI strip (epoch, loss, mAP50, mAP50-95, precision, recall).
Middle: two charts side-by-side (loss curve · mAP curve).
Bottom: terminal-style log.

Training itself runs in TrainTask (core/workers/ml_worker.py). The default
implementation is a mock loop that emits realistic curves; the screen is
already wired to consume the real rf-detr signals when swapped in.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QThreadPool
from PyQt6.QtGui import QColor, QFont, QTextCursor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from pidlens.core.workers.ml_worker import TrainConfig, TrainTask
from pidlens.data.runs import RunRecord, new_run_id, write_run
from pidlens.data.workspace import Workspace
from pidlens.gui.components.charts import Sparkline
from pidlens.gui.components.widgets import StatBlock, primary_button
from pidlens.gui.screens._base import Screen


class TrainingScreen(Screen):
    title = "Training"

    def _build(self) -> None:
        self.workspace: Workspace | None = None
        self.pool = QThreadPool.globalInstance()
        self.task: TrainTask | None = None
        self.current_run: RunRecord | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top toolbar ──────────────────────────────────────
        toolbar = QToolBar()
        bar_holder = QWidget()
        bar_lay = QHBoxLayout(bar_holder)
        bar_lay.setContentsMargins(12, 6, 12, 6)
        bar_lay.setSpacing(8)

        bar_lay.addWidget(QLabel("Epochs"))
        self.epochs_spin = QSpinBox()
        self.epochs_spin.setRange(1, 1000)
        self.epochs_spin.setValue(30)
        bar_lay.addWidget(self.epochs_spin)

        bar_lay.addWidget(QLabel("Batch"))
        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(1, 256)
        self.batch_spin.setValue(16)
        bar_lay.addWidget(self.batch_spin)

        bar_lay.addWidget(QLabel("Image size"))
        self.imgsz_spin = QSpinBox()
        self.imgsz_spin.setRange(64, 2048)
        self.imgsz_spin.setSingleStep(32)
        self.imgsz_spin.setValue(640)
        bar_lay.addWidget(self.imgsz_spin)

        bar_lay.addWidget(QLabel("Seed"))
        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(0, 2**31 - 1)
        self.seed_spin.setValue(42)
        bar_lay.addWidget(self.seed_spin)

        bar_lay.addStretch(1)
        self.start_btn = primary_button("Start training")
        self.start_btn.clicked.connect(self._on_start)
        bar_lay.addWidget(self.start_btn)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop)
        bar_lay.addWidget(self.stop_btn)

        toolbar.addWidget(bar_holder)
        root.addWidget(toolbar)

        # ── KPI strip ────────────────────────────────────────
        kpi_row = QHBoxLayout()
        kpi_row.setContentsMargins(16, 12, 16, 0)
        kpi_row.setSpacing(8)
        self.kpi_epoch = StatBlock("epoch", "0", "of 0")
        self.kpi_loss = StatBlock("loss", "—", "")
        self.kpi_map = StatBlock("mAP50", "—", "")
        self.kpi_map95 = StatBlock("mAP50-95", "—", "")
        self.kpi_prec = StatBlock("precision", "—", "")
        self.kpi_recall = StatBlock("recall", "—", "")
        for s in (
            self.kpi_epoch,
            self.kpi_loss,
            self.kpi_map,
            self.kpi_map95,
            self.kpi_prec,
            self.kpi_recall,
        ):
            kpi_row.addWidget(s, 1)
        root.addLayout(kpi_row)

        # ── Two charts ───────────────────────────────────────
        charts_row = QHBoxLayout()
        charts_row.setContentsMargins(16, 12, 16, 0)
        charts_row.setSpacing(12)
        self.loss_chart = Sparkline()
        self.loss_chart.set_series("loss", [], QColor("#c96442"))
        self.map_chart = Sparkline()
        self.map_chart.set_series("mAP50", [], QColor("#3a8a4a"))
        charts_row.addWidget(self.loss_chart, 1)
        charts_row.addWidget(self.map_chart, 1)
        root.addLayout(charts_row, 1)

        # ── Terminal log ─────────────────────────────────────
        log_holder = QVBoxLayout()
        log_holder.setContentsMargins(16, 12, 16, 16)
        log_holder.setSpacing(4)
        log_holder.addWidget(QLabel("Log"))
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setObjectName("training-log")
        mono = QFont("JetBrains Mono")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        mono.setPointSize(11)
        self.log.setFont(mono)
        self.log.setStyleSheet("background:#1d1a14;color:#e6dcc8;border-radius:6px;padding:8px;")
        log_holder.addWidget(self.log, 1)
        root.addLayout(log_holder, 1)

        self.signals.workspaceOpened.connect(self._on_workspace_opened)

        # In-memory series for the charts.
        self._losses: list[float] = []
        self._maps: list[float] = []

    # ── Workspace ────────────────────────────────────────────
    def _on_workspace_opened(self, ws: Workspace) -> None:
        self.workspace = ws

    # ── Start / Stop ─────────────────────────────────────────
    def _on_start(self) -> None:
        if self.workspace is None:
            self.signals.status.emit("open a workspace first", "warn")
            return
        if self.task is not None:
            return
        run_id = new_run_id()
        cfg = TrainConfig(
            run_id=run_id,
            workspace_root=self.workspace.root,
            data_yaml=self.workspace.data_yaml,
            epochs=self.epochs_spin.value(),
            batch_size=self.batch_spin.value(),
            image_size=self.imgsz_spin.value(),
            seed=self.seed_spin.value(),
            output_dir=self.workspace.runs_dir / run_id,
        )
        self.current_run = RunRecord(
            run_id=run_id,
            workspace_root=self.workspace.root,
            config={
                "epochs": cfg.epochs,
                "batch_size": cfg.batch_size,
                "image_size": cfg.image_size,
                "seed": cfg.seed,
                "data_yaml": str(cfg.data_yaml),
            },
        )
        self.task = TrainTask(cfg)
        self.task.signals.started.connect(self._on_started)
        self.task.signals.epoch.connect(self._on_epoch)
        self.task.signals.log.connect(self._on_log)
        self.task.signals.finished.connect(self._on_finished)
        self.task.signals.failed.connect(self._on_failed)

        self._losses.clear()
        self._maps.clear()
        self.log.clear()
        self.loss_chart.set_series("loss", [])
        self.map_chart.set_series("mAP50", [])
        self.kpi_epoch.set_value("0")
        self.kpi_epoch.set_sub(f"of {cfg.epochs}")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.pool.start(self.task)

    def _on_stop(self) -> None:
        if self.task is not None:
            self.task.cancel()

    # ── Signal handlers ──────────────────────────────────────
    def _on_started(self, run_id: str) -> None:
        self._append_log(f"started {run_id}")

    def _on_epoch(self, run_id: str, epoch: int, metrics: dict) -> None:
        self._losses.append(metrics.get("loss", 0.0))
        self._maps.append(metrics.get("mAP50", 0.0))
        self.loss_chart.set_series("loss", self._losses, QColor("#c96442"))
        self.map_chart.set_series("mAP50", self._maps, QColor("#3a8a4a"))
        self.kpi_epoch.set_value(str(epoch))
        self.kpi_loss.set_value(f"{metrics.get('loss', 0):.3f}")
        self.kpi_map.set_value(f"{metrics.get('mAP50', 0):.3f}")
        self.kpi_map95.set_value(f"{metrics.get('mAP50-95', 0):.3f}")
        self.kpi_prec.set_value(f"{metrics.get('precision', 0):.3f}")
        self.kpi_recall.set_value(f"{metrics.get('recall', 0):.3f}")
        if self.current_run is not None:
            self.current_run.history.append({"epoch": epoch, **metrics})
        self.signals.trainingTick.emit(run_id, epoch, metrics)

    def _on_log(self, _run_id: str, line: str) -> None:
        self._append_log(line)

    def _on_finished(self, run_id: str, summary: dict) -> None:
        self._append_log(f"finished {run_id}")
        if self.current_run is not None:
            self.current_run.summary = summary
            write_run(self.current_run)
        self.task = None
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.signals.trainingFinished.emit(run_id, summary)

    def _on_failed(self, run_id: str, err: str) -> None:
        self._append_log(f"FAILED {run_id}: {err}")
        self.task = None
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.signals.status.emit(f"training failed: {err}", "error")

    def _append_log(self, line: str) -> None:
        self.log.appendPlainText(line)
        self.log.moveCursor(QTextCursor.MoveOperation.End)
