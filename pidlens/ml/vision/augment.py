"""Training-time augmentations.

Each aug is a pure function (img, rng) → img. The registry mirrors the
preprocessing-ops pattern so the UI can render them with one shared widget.
Augmentations are applied at training time only — they don't write to disk.
"""

from __future__ import annotations

import random
from typing import Callable

import cv2
import numpy as np


def aug_hflip(img: np.ndarray, rng: random.Random, *, p: float = 0.5) -> np.ndarray:
    return cv2.flip(img, 1) if rng.random() < p else img


def aug_vflip(img: np.ndarray, rng: random.Random, *, p: float = 0.5) -> np.ndarray:
    return cv2.flip(img, 0) if rng.random() < p else img


def aug_rotate(img: np.ndarray, rng: random.Random, *, max_deg: float = 15.0) -> np.ndarray:
    if max_deg <= 0:
        return img
    angle = rng.uniform(-max_deg, max_deg)
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT_101)


def aug_brightness(img: np.ndarray, rng: random.Random, *, max_delta: float = 0.25) -> np.ndarray:
    if max_delta <= 0:
        return img
    delta = rng.uniform(-max_delta, max_delta) * 255
    return np.clip(img.astype(np.int16) + int(delta), 0, 255).astype(np.uint8)


def aug_contrast(img: np.ndarray, rng: random.Random, *, max_delta: float = 0.25) -> np.ndarray:
    if max_delta <= 0:
        return img
    factor = 1.0 + rng.uniform(-max_delta, max_delta)
    mean = img.mean()
    out = (img.astype(np.float32) - mean) * factor + mean
    return np.clip(out, 0, 255).astype(np.uint8)


def aug_noise(img: np.ndarray, rng: random.Random, *, sigma: float = 8.0) -> np.ndarray:
    if sigma <= 0:
        return img
    rs = np.random.default_rng(rng.randint(0, 2**31 - 1))
    noise = rs.normal(0, sigma, img.shape).astype(np.int16)
    return np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)


def aug_blur(img: np.ndarray, rng: random.Random, *, max_kernel: int = 5) -> np.ndarray:
    if max_kernel < 3:
        return img
    k = rng.choice([3, 5, 7][: max(1, max_kernel // 2)])
    return cv2.GaussianBlur(img, (k, k), 0)


AugFn = Callable[..., np.ndarray]

AUGS: dict[str, dict] = {
    "hflip":      {"fn": aug_hflip,      "label": "Horizontal flip",  "params": {"p": 0.5}},
    "vflip":      {"fn": aug_vflip,      "label": "Vertical flip",    "params": {"p": 0.5}},
    "rotate":     {"fn": aug_rotate,     "label": "Rotate",           "params": {"max_deg": 15.0}},
    "brightness": {"fn": aug_brightness, "label": "Brightness jitter","params": {"max_delta": 0.25}},
    "contrast":   {"fn": aug_contrast,   "label": "Contrast jitter",  "params": {"max_delta": 0.25}},
    "noise":      {"fn": aug_noise,      "label": "Gaussian noise",   "params": {"sigma": 8.0}},
    "blur":       {"fn": aug_blur,       "label": "Gaussian blur",    "params": {"max_kernel": 5}},
}


def apply_chain(img: np.ndarray, chain: list[tuple[str, dict]], seed: int) -> np.ndarray:
    rng = random.Random(seed)
    out = img
    for aug_id, params in chain:
        spec = AUGS.get(aug_id)
        if not spec:
            continue
        merged = {**spec["params"], **(params or {})}
        out = spec["fn"](out, rng, **merged)
    return out
