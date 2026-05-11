"""Background OpenCV/image-processing tasks for the preprocessing pipeline.

The pipeline applies an ordered list of ops to one image. Each op gets a
(image, boxes_xyxy, scope_mask) triple and returns the same triple — keeping
the contract uniform means a UI checkbox flipping an op from global to
per-box doesn't need a different worker shape.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import cv2
import numpy as np
from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

from pidlens.data.workspace import ImageEntry
from pidlens.data.yolo_parser import read_labels
from pidlens.data.yaml_manager import PreprocessMeta, PreprocessOp, write_meta
from pidlens.ml.vision.morphology import apply_op


class _VisionSignals(QObject):
    finished = pyqtSignal(object, object)  # source_path, ndarray (result)
    progress = pyqtSignal(object, int, int)  # source_path, step_index, n_steps
    failed = pyqtSignal(object, str)


class VisionPipelineTask(QRunnable):
    """Apply a sequence of (op_id, scope, params) to one image."""

    def __init__(
        self,
        src_path: Path,
        ops: list[tuple[str, str, dict]],
        boxes_xyxy: list[tuple[int, int, int, int]] | None = None,
    ) -> None:
        super().__init__()
        self.src_path = src_path
        self.ops = ops
        self.boxes_xyxy = boxes_xyxy or []
        self.signals = _VisionSignals()

    def run(self) -> None:
        try:
            buf = np.fromfile(str(self.src_path), dtype=np.uint8)
            img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
            if img is None:
                raise RuntimeError("cv2 returned None")
            n = len(self.ops)
            for i, (op_id, scope, params) in enumerate(self.ops):
                img = apply_op(img, op_id, scope, params, self.boxes_xyxy)
                self.signals.progress.emit(self.src_path, i + 1, n)
            self.signals.finished.emit(self.src_path, img)
        except Exception as e:  # noqa: BLE001
            self.signals.failed.emit(self.src_path, str(e))


# ── Batch preprocess ─────────────────────────────────────────
class _BatchSignals(QObject):
    started = pyqtSignal(object)              # version_dir
    progress = pyqtSignal(object, int, int)   # version_dir, done, total
    finished = pyqtSignal(object)             # version_dir
    failed = pyqtSignal(object, str)


class BatchPreprocessTask(QRunnable):
    """Run the pipeline over every workspace image; write a versioned dir.

    Output layout:
        version_dir/
            meta.yaml
            images/<stem>.png      (PNG so threshold/binary ops survive cleanly)
            labels/<stem>.txt      (copied unchanged from source)
    """

    def __init__(
        self,
        entries: list[ImageEntry],
        ops: list[tuple[str, str, dict]],
        version_dir: Path,
        *,
        seed: int = 42,
        parent_version: str | None = None,
    ) -> None:
        super().__init__()
        self.entries = entries
        self.ops = ops
        self.version_dir = version_dir
        self.seed = seed
        self.parent_version = parent_version
        self.signals = _BatchSignals()
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        try:
            out_imgs = self.version_dir / "images"
            out_lbls = self.version_dir / "labels"
            out_imgs.mkdir(parents=True, exist_ok=True)
            out_lbls.mkdir(parents=True, exist_ok=True)
            self.signals.started.emit(self.version_dir)

            total = len(self.entries)
            label_count = 0
            for i, entry in enumerate(self.entries):
                if self._cancel:
                    break

                buf = np.fromfile(str(entry.image), dtype=np.uint8)
                img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
                if img is None:
                    continue

                boxes_xyxy: list[tuple[int, int, int, int]] = []
                if entry.has_label and entry.label is not None:
                    h, w = img.shape[:2]
                    for b in read_labels(entry.label):
                        boxes_xyxy.append(b.to_pixel_xyxy(w, h))

                for op_id, scope, params in self.ops:
                    img = apply_op(img, op_id, scope, params, boxes_xyxy)

                ok, encoded = cv2.imencode(".png", img)
                if not ok:
                    continue
                out_img = out_imgs / f"{entry.stem}.png"
                out_img.write_bytes(encoded.tobytes())

                if entry.has_label and entry.label is not None:
                    shutil.copy2(entry.label, out_lbls / f"{entry.stem}.txt")
                    label_count += 1

                self.signals.progress.emit(self.version_dir, i + 1, total)

            meta = PreprocessMeta(
                parent=self.parent_version,
                seed=self.seed,
                ops=[PreprocessOp(id=op, scope=scope, params=params) for op, scope, params in self.ops],
                counts={"images": total, "labels": label_count},
            )
            write_meta(self.version_dir, meta)
            self.signals.finished.emit(self.version_dir)
        except Exception as e:  # noqa: BLE001
            self.signals.failed.emit(self.version_dir, str(e))
