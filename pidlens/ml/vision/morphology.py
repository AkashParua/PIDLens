"""Image transforms used by the preprocessing pipeline.

Each op has a stable string id (used in meta.yaml so reruns are reproducible)
and either global or per-box scope. The dispatch table at the bottom is the
authoritative list of available ops; the UI reads it to populate the picker.

Per-box ops crop, transform, paste back. Global ops act on the whole frame.
Geometric ops (resize) are global-only — box coordinates remap automatically.
"""

from __future__ import annotations

from typing import Callable

import cv2
import numpy as np


# ── Op implementations ───────────────────────────────────────
# Signature: (img: np.ndarray, **params) -> np.ndarray

def op_threshold(img: np.ndarray, *, method: str = "otsu", thresh: int = 127) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    if method == "otsu":
        _, out = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif method == "adaptive":
        out = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
    else:
        _, out = cv2.threshold(gray, int(thresh), 255, cv2.THRESH_BINARY)
    return cv2.cvtColor(out, cv2.COLOR_GRAY2BGR) if img.ndim == 3 else out


def _kernel(size: int) -> np.ndarray:
    size = max(1, int(size))
    if size % 2 == 0:
        size += 1
    return cv2.getStructuringElement(cv2.MORPH_RECT, (size, size))


def op_morph_open(img: np.ndarray, *, kernel: int = 3, iterations: int = 1) -> np.ndarray:
    return cv2.morphologyEx(img, cv2.MORPH_OPEN, _kernel(kernel), iterations=int(iterations))


def op_morph_close(img: np.ndarray, *, kernel: int = 3, iterations: int = 1) -> np.ndarray:
    return cv2.morphologyEx(img, cv2.MORPH_CLOSE, _kernel(kernel), iterations=int(iterations))


def op_dilate(img: np.ndarray, *, kernel: int = 3, iterations: int = 1) -> np.ndarray:
    return cv2.dilate(img, _kernel(kernel), iterations=int(iterations))


def op_erode(img: np.ndarray, *, kernel: int = 3, iterations: int = 1) -> np.ndarray:
    return cv2.erode(img, _kernel(kernel), iterations=int(iterations))


def op_blur(img: np.ndarray, *, kernel: int = 3) -> np.ndarray:
    k = max(1, int(kernel))
    if k % 2 == 0:
        k += 1
    return cv2.GaussianBlur(img, (k, k), 0)


def op_resize(img: np.ndarray, *, width: int = 0, height: int = 0, scale: float = 0.0) -> np.ndarray:
    h, w = img.shape[:2]
    if scale > 0:
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))
    else:
        new_w = int(width) if width else w
        new_h = int(height) if height else h
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


def op_invert(img: np.ndarray) -> np.ndarray:
    return cv2.bitwise_not(img)


def op_grayscale(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return img
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def op_canny(img: np.ndarray, *, low: int = 100, high: int = 200) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    edges = cv2.Canny(gray, int(low), int(high))
    return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR) if img.ndim == 3 else edges


def op_fill_holes(img: np.ndarray) -> np.ndarray:
    """Flood-fill from the borders, then invert and OR — fills interior holes."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    h, w = binary.shape
    flood = binary.copy()
    mask = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(flood, mask, (0, 0), 255)
    filled = binary | cv2.bitwise_not(flood)
    return cv2.cvtColor(filled, cv2.COLOR_GRAY2BGR) if img.ndim == 3 else filled


# ── Registry ──────────────────────────────────────────────────
OpFn = Callable[..., np.ndarray]

OPS: dict[str, dict] = {
    "threshold":   {"fn": op_threshold,   "label": "Threshold",        "scopes": ("global", "per-box"), "params": {"method": "otsu", "thresh": 127}},
    "morph-open":  {"fn": op_morph_open,  "label": "Morphology · Open",  "scopes": ("global", "per-box"), "params": {"kernel": 3, "iterations": 1}},
    "morph-close": {"fn": op_morph_close, "label": "Morphology · Close", "scopes": ("global", "per-box"), "params": {"kernel": 3, "iterations": 1}},
    "dilate":      {"fn": op_dilate,      "label": "Dilate",             "scopes": ("global", "per-box"), "params": {"kernel": 3, "iterations": 1}},
    "erode":       {"fn": op_erode,       "label": "Erode",              "scopes": ("global", "per-box"), "params": {"kernel": 3, "iterations": 1}},
    "blur":        {"fn": op_blur,        "label": "Gaussian blur",      "scopes": ("global", "per-box"), "params": {"kernel": 3}},
    "resize":      {"fn": op_resize,      "label": "Resize",             "scopes": ("global",),           "params": {"scale": 1.0, "width": 0, "height": 0}},
    "invert":      {"fn": op_invert,      "label": "Invert",             "scopes": ("global", "per-box"), "params": {}},
    "grayscale":   {"fn": op_grayscale,   "label": "Grayscale",          "scopes": ("global",),           "params": {}},
    "canny":       {"fn": op_canny,       "label": "Canny edges",        "scopes": ("global", "per-box"), "params": {"low": 100, "high": 200}},
    "fill-holes":  {"fn": op_fill_holes,  "label": "Fill holes",         "scopes": ("global", "per-box"), "params": {}},
}


def list_op_ids() -> list[str]:
    return list(OPS.keys())


def get_op(op_id: str) -> dict:
    if op_id not in OPS:
        raise KeyError(f"unknown op: {op_id}")
    return OPS[op_id]


def apply_op(
    img: np.ndarray,
    op_id: str,
    scope: str,
    params: dict,
    boxes_xyxy: list[tuple[int, int, int, int]] | None = None,
) -> np.ndarray:
    """Apply one op. For per-box scope, run on each box's crop and paste back.

    The image is copied so callers can rely on the input not being mutated.
    """
    spec = get_op(op_id)
    fn: OpFn = spec["fn"]
    merged = {**spec["params"], **(params or {})}

    if scope == "global" or not boxes_xyxy or scope not in spec["scopes"]:
        return fn(img.copy(), **merged)

    out = img.copy()
    h, w = out.shape[:2]
    for x1, y1, x2, y2 in boxes_xyxy:
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 <= x1 or y2 <= y1:
            continue
        crop = out[y1:y2, x1:x2]
        transformed = fn(crop.copy(), **merged)
        # If the op changed the crop shape (shouldn't for per-box ops, but
        # resize sneaks in via custom scripts) snap it back to the box's size.
        if transformed.shape[:2] != crop.shape[:2]:
            transformed = cv2.resize(transformed, (crop.shape[1], crop.shape[0]))
        if transformed.ndim == 2 and out.ndim == 3:
            transformed = cv2.cvtColor(transformed, cv2.COLOR_GRAY2BGR)
        out[y1:y2, x1:x2] = transformed
    return out
