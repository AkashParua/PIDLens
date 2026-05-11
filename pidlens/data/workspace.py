"""Workspace = a root directory that holds images, labels, and metadata.

Layout (all paths relative to `root`):
    images/                  raw input images (or ./ if the user picked a flat
                             folder — see Workspace.scan)
    labels/                  YOLOv8 .txt files, one per image, same stem
    data.yaml                class names + dataset descriptor
    preprocess/v{N}/         versioned outputs of the preprocessing pipeline
    preprocess/v{N}/meta.yaml
    runs/{run_id}/           training run artifacts
    models/                  exported / registered model weights

A Workspace never mutates the user's original images. All transforms produce
new files in `preprocess/v{N}/`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pidlens.config import (
    IMAGE_EXTS,
    WORKSPACE_DATA_YAML,
    WORKSPACE_IMAGES_DIR,
    WORKSPACE_LABELS_DIR,
    WORKSPACE_MODELS_DIR,
    WORKSPACE_PREPROCESS_DIR,
    WORKSPACE_RUNS_DIR,
)


@dataclass
class ImageEntry:
    """One scanned image and any label file that pairs with it by stem."""

    image: Path
    label: Path | None = None
    width: int | None = None  # filled in lazily by Triage thumbnail load
    height: int | None = None

    @property
    def stem(self) -> str:
        return self.image.stem

    @property
    def has_label(self) -> bool:
        return self.label is not None and self.label.exists()


@dataclass
class Workspace:
    root: Path
    images: list[ImageEntry] = field(default_factory=list)
    orphan_labels: list[Path] = field(default_factory=list)
    class_names: list[str] = field(default_factory=list)

    # ── Computed paths ────────────────────────────────────────
    @property
    def images_dir(self) -> Path:
        d = self.root / WORKSPACE_IMAGES_DIR
        return d if d.exists() else self.root

    @property
    def labels_dir(self) -> Path:
        return self.root / WORKSPACE_LABELS_DIR

    @property
    def data_yaml(self) -> Path:
        return self.root / WORKSPACE_DATA_YAML

    @property
    def preprocess_dir(self) -> Path:
        return self.root / WORKSPACE_PREPROCESS_DIR

    @property
    def runs_dir(self) -> Path:
        return self.root / WORKSPACE_RUNS_DIR

    @property
    def models_dir(self) -> Path:
        return self.root / WORKSPACE_MODELS_DIR

    # ── Scanning ──────────────────────────────────────────────
    def scan(self) -> None:
        """Re-read images, labels, and class names from disk.

        Supports two layouts: a YOLO-style folder with images/ + labels/, or a
        flat folder of images (labels are then expected alongside each image
        with the same stem and .txt extension).
        """
        self.images.clear()
        self.orphan_labels.clear()

        img_dir = self.images_dir
        lbl_dir = self.labels_dir if self.labels_dir.exists() else img_dir

        image_paths: list[Path] = []
        for p in sorted(img_dir.rglob("*")):
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
                image_paths.append(p)

        used_labels: set[Path] = set()
        for img in image_paths:
            lbl_candidate = lbl_dir / f"{img.stem}.txt"
            if not lbl_candidate.exists():
                # also tolerate label sitting next to image (flat layout)
                lbl_candidate = img.with_suffix(".txt")
            entry = ImageEntry(image=img)
            if lbl_candidate.exists():
                entry.label = lbl_candidate
                used_labels.add(lbl_candidate.resolve())
            self.images.append(entry)

        # Orphan labels: .txt files in labels_dir that don't pair with an image
        if lbl_dir.exists():
            for p in sorted(lbl_dir.rglob("*.txt")):
                if p.resolve() not in used_labels:
                    self.orphan_labels.append(p)

        # Class names from data.yaml if present; deferred parsing avoids a
        # hard pyyaml import at module load.
        self.class_names = self._read_class_names()

    def _read_class_names(self) -> list[str]:
        if not self.data_yaml.exists():
            return []
        import yaml

        try:
            data = yaml.safe_load(self.data_yaml.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            return []
        names = data.get("names", [])
        if isinstance(names, dict):
            # yolov5 style: {0: "a", 1: "b"} → list ordered by key
            return [names[k] for k in sorted(names.keys())]
        if isinstance(names, list):
            return [str(n) for n in names]
        return []

    # ── Stats convenience ─────────────────────────────────────
    @property
    def total(self) -> int:
        return len(self.images)

    @property
    def annotated(self) -> int:
        return sum(1 for e in self.images if e.has_label)

    @property
    def unannotated(self) -> int:
        return self.total - self.annotated
