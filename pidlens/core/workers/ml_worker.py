"""Training and inference workers.

The rf-detr training loop is stubbed with a mock that emits realistic-looking
loss / mAP curves so the Training screen can be developed end-to-end without
the real dependency installed. To wire in the real `rfdetr` package, replace
the body of `_mock_train` — the signal contract stays the same.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from pathlib import Path

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal


@dataclass
class TrainConfig:
    run_id: str
    workspace_root: Path
    data_yaml: Path
    epochs: int = 30
    batch_size: int = 16
    image_size: int = 640
    lr: float = 1e-4
    seed: int = 42
    output_dir: Path | None = None  # defaults to workspace/runs/<run_id>
    extra: dict = field(default_factory=dict)


class _TrainSignals(QObject):
    started = pyqtSignal(str)                       # run_id
    epoch = pyqtSignal(str, int, dict)              # run_id, epoch_idx, metrics
    log = pyqtSignal(str, str)                       # run_id, line
    finished = pyqtSignal(str, dict)                 # run_id, summary
    failed = pyqtSignal(str, str)                    # run_id, error


class TrainTask(QRunnable):
    """Mock training. Replace `_mock_train` with `rfdetr` integration later."""

    def __init__(self, config: TrainConfig) -> None:
        super().__init__()
        self.config = config
        self.signals = _TrainSignals()
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        cfg = self.config
        try:
            self.signals.started.emit(cfg.run_id)
            self._mock_train(cfg)
        except Exception as e:  # noqa: BLE001
            self.signals.failed.emit(cfg.run_id, str(e))

    # ── Real integration goes here ────────────────────────────
    # def _real_train(self, cfg: TrainConfig) -> None:
    #     from rfdetr import RFDETRBase
    #     model = RFDETRBase()
    #     for epoch, metrics in model.train(
    #         dataset_dir=str(cfg.workspace_root),
    #         epochs=cfg.epochs, batch_size=cfg.batch_size, ...
    #     ):
    #         if self._cancel: break
    #         self.signals.epoch.emit(cfg.run_id, epoch, metrics)
    #     self.signals.finished.emit(cfg.run_id, model.last_metrics)

    # ── Mock ──────────────────────────────────────────────────
    def _mock_train(self, cfg: TrainConfig) -> None:
        """Emit synthetic per-epoch metrics. Loss decays, mAP grows + noise."""
        import random

        rng = random.Random(cfg.seed)
        loss = 2.4
        map50 = 0.05
        history: list[dict] = []

        for epoch in range(1, cfg.epochs + 1):
            if self._cancel:
                self.signals.log.emit(cfg.run_id, f"epoch {epoch}: cancelled")
                break
            time.sleep(0.4)  # simulate work; replace with real iteration cost
            # exponential decay + noise
            loss = max(0.05, loss * 0.93 + rng.uniform(-0.05, 0.05))
            map50 = min(0.95, map50 + (0.95 - map50) * 0.08 + rng.uniform(-0.01, 0.01))
            map50_95 = max(0.0, map50 * 0.65 + rng.uniform(-0.01, 0.01))
            precision = min(0.99, 0.4 + (1 - math.exp(-epoch / 8)) * 0.55)
            recall = min(0.99, 0.35 + (1 - math.exp(-epoch / 9)) * 0.55)

            metrics = {
                "loss": round(loss, 4),
                "mAP50": round(map50, 4),
                "mAP50-95": round(map50_95, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "lr": cfg.lr,
            }
            history.append({"epoch": epoch, **metrics})
            self.signals.epoch.emit(cfg.run_id, epoch, metrics)
            self.signals.log.emit(
                cfg.run_id,
                f"epoch {epoch:>3}/{cfg.epochs}  loss={metrics['loss']:.3f}  "
                f"mAP50={metrics['mAP50']:.3f}  mAP50-95={metrics['mAP50-95']:.3f}",
            )

        summary = {
            "epochs_completed": len(history),
            "best": max(history, key=lambda r: r["mAP50"], default={}),
            "final": history[-1] if history else {},
            "history": history,
        }
        self.signals.finished.emit(cfg.run_id, summary)
