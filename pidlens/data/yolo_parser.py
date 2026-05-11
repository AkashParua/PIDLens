"""YOLOv8 label format I/O.

Per-image text file, one line per box:
    class_id cx cy w h
where (cx, cy, w, h) are normalized to [0, 1] and (cx, cy) is the box centre.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml


@dataclass
class YoloBox:
    class_id: int
    cx: float  # 0..1, centre x
    cy: float  # 0..1, centre y
    w: float   # 0..1
    h: float   # 0..1

    # ── Conversions ───────────────────────────────────────────
    def to_pixel_xyxy(self, img_w: int, img_h: int) -> tuple[int, int, int, int]:
        """Return (x1, y1, x2, y2) in absolute pixels."""
        x1 = (self.cx - self.w / 2) * img_w
        y1 = (self.cy - self.h / 2) * img_h
        x2 = (self.cx + self.w / 2) * img_w
        y2 = (self.cy + self.h / 2) * img_h
        return int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))

    @classmethod
    def from_pixel_xyxy(
        cls, class_id: int, x1: float, y1: float, x2: float, y2: float, img_w: int, img_h: int
    ) -> "YoloBox":
        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1
        cx = ((x1 + x2) / 2) / img_w
        cy = ((y1 + y2) / 2) / img_h
        w = (x2 - x1) / img_w
        h = (y2 - y1) / img_h
        return cls(class_id=class_id, cx=cx, cy=cy, w=w, h=h)


def read_labels(path: Path) -> list[YoloBox]:
    if not path.exists():
        return []
    boxes: list[YoloBox] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 5:
            # malformed; skip silently — Triage will flag missing/orphan data
            continue
        try:
            cid = int(parts[0])
            cx, cy, w, h = (float(x) for x in parts[1:5])
        except ValueError:
            continue
        boxes.append(YoloBox(class_id=cid, cx=cx, cy=cy, w=w, h=h))
    return boxes


def write_labels(path: Path, boxes: Iterable[YoloBox]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for b in boxes:
        lines.append(f"{b.class_id} {b.cx:.6f} {b.cy:.6f} {b.w:.6f} {b.h:.6f}")
    # Trailing newline keeps text-mode diffs clean; empty file is valid YOLO
    # (means "no boxes on this image"), distinct from a missing file (which
    # we read as "un-annotated").
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


# ── data.yaml ─────────────────────────────────────────────────
def read_data_yaml(path: Path) -> dict:
    """Parse data.yaml. Tolerant of both list and dict 'names' shapes."""
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    names = data.get("names", [])
    if isinstance(names, dict):
        names = [names[k] for k in sorted(names.keys())]
    data["names"] = [str(n) for n in (names or [])]
    return data


def write_data_yaml(
    path: Path,
    names: list[str],
    *,
    train: str | None = None,
    val: str | None = None,
    test: str | None = None,
    root: str | None = None,
) -> None:
    payload: dict = {"names": names, "nc": len(names)}
    if root is not None:
        payload["path"] = root
    if train is not None:
        payload["train"] = train
    if val is not None:
        payload["val"] = val
    if test is not None:
        payload["test"] = test
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
