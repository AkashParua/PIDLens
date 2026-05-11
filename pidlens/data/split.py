"""Train / val / test split, optionally stratified by dominant class.

For each image we compute its "primary class" as the most-frequent class in
its label file (deterministic tie-break by lowest id). Images with no label
go into an "unlabeled" bucket and are excluded from the stratified pool —
they'd add noise to the per-class balance.
"""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from pidlens.data.workspace import ImageEntry, Workspace
from pidlens.data.yolo_parser import read_labels


@dataclass
class SplitResult:
    train: list[Path] = field(default_factory=list)
    val: list[Path] = field(default_factory=list)
    test: list[Path] = field(default_factory=list)
    unlabeled: list[Path] = field(default_factory=list)
    # per-class (train, val, test) box counts — fuels the stacked bar chart.
    per_class_boxes: dict[int, tuple[int, int, int]] = field(default_factory=dict)


def _primary_class(entry: ImageEntry) -> int | None:
    if not entry.has_label or entry.label is None:
        return None
    boxes = read_labels(entry.label)
    if not boxes:
        return None
    counts = Counter(b.class_id for b in boxes)
    # Counter.most_common is stable; tie-break by lowest id is what we want.
    best, best_count = min(
        ((cid, cnt) for cid, cnt in counts.items()),
        key=lambda kv: (-kv[1], kv[0]),
    )
    return best


def compute_split(
    workspace: Workspace,
    train: float = 0.7,
    val: float = 0.15,
    test: float = 0.15,
    *,
    stratified: bool = True,
    seed: int = 42,
) -> SplitResult:
    total = max(0.0001, train + val + test)
    train, val, test = train / total, val / total, test / total

    rng = random.Random(seed)
    result = SplitResult()

    by_class: dict[int | None, list[ImageEntry]] = defaultdict(list)
    for entry in workspace.images:
        by_class[_primary_class(entry)].append(entry)

    result.unlabeled = [e.image for e in by_class.pop(None, [])]

    pools: list[list[ImageEntry]]
    if stratified:
        pools = [list(v) for v in by_class.values()]
    else:
        flat: list[ImageEntry] = []
        for v in by_class.values():
            flat.extend(v)
        pools = [flat]

    for pool in pools:
        rng.shuffle(pool)
        n = len(pool)
        n_train = int(round(n * train))
        n_val = int(round(n * val))
        # test absorbs rounding remainder.
        n_test = n - n_train - n_val
        if n_test < 0:
            n_val += n_test
            n_test = 0
        result.train.extend(e.image for e in pool[:n_train])
        result.val.extend(e.image for e in pool[n_train:n_train + n_val])
        result.test.extend(e.image for e in pool[n_train + n_val:])

    # Per-class box totals across the splits.
    per_class: dict[int, list[int]] = defaultdict(lambda: [0, 0, 0])
    bucket_paths = (
        (0, set(result.train)),
        (1, set(result.val)),
        (2, set(result.test)),
    )
    for entry in workspace.images:
        if not entry.has_label or entry.label is None:
            continue
        for idx, paths in bucket_paths:
            if entry.image in paths:
                for b in read_labels(entry.label):
                    per_class[b.class_id][idx] += 1
                break
    result.per_class_boxes = {k: tuple(v) for k, v in per_class.items()}
    return result


def write_split_lists(workspace: Workspace, split: SplitResult) -> dict[str, Path]:
    """Write train.txt / val.txt / test.txt with absolute image paths."""
    out: dict[str, Path] = {}
    for name, paths in (("train", split.train), ("val", split.val), ("test", split.test)):
        p = workspace.root / f"{name}.txt"
        p.write_text("\n".join(str(x) for x in paths) + ("\n" if paths else ""), encoding="utf-8")
        out[name] = p
    return out
