"""YAML helpers for preprocessing-pipeline metadata.

Each preprocessing run writes a directory like:
    <root>/preprocess/v3/
        meta.yaml
        images/...     (transformed images, original stems preserved)
        labels/...     (boxes remapped through any geometric ops; for box-local
                        ops the labels are copied unchanged)

meta.yaml schema (versioned via the top-level 'schema' key):

    schema: 1
    parent: ./v2          # null for v1
    created: 2025-11-12T10:34:00Z
    seed: 42              # reproducible ops
    ops:
      - id: threshold-otsu
        scope: global     # or 'per-box'
        params: { thresh: 'otsu' }
      - id: morph-open
        scope: global
        params: { kernel: 3, iterations: 1 }
    counts:
      images: 642
      labels: 318
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


META_FILENAME = "meta.yaml"
VERSION_RE = re.compile(r"^v(\d+)$")


@dataclass
class PreprocessOp:
    id: str
    scope: str  # "global" | "per-box"
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class PreprocessMeta:
    schema: int = 1
    parent: str | None = None
    created: str = ""
    seed: int | None = None
    ops: list[PreprocessOp] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "schema": self.schema,
            "parent": self.parent,
            "created": self.created or now_iso(),
            "seed": self.seed,
            "ops": [{"id": op.id, "scope": op.scope, "params": op.params} for op in self.ops],
            "counts": dict(self.counts),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PreprocessMeta":
        ops = [
            PreprocessOp(id=o.get("id", ""), scope=o.get("scope", "global"), params=o.get("params", {}) or {})
            for o in (data.get("ops") or [])
        ]
        return cls(
            schema=int(data.get("schema", 1)),
            parent=data.get("parent"),
            created=str(data.get("created", "")),
            seed=data.get("seed"),
            ops=ops,
            counts=dict(data.get("counts") or {}),
        )


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def next_version_dir(preprocess_root: Path) -> Path:
    """Return the next vN directory (not created on disk)."""
    preprocess_root.mkdir(parents=True, exist_ok=True)
    n = 0
    for child in preprocess_root.iterdir():
        if not child.is_dir():
            continue
        m = VERSION_RE.match(child.name)
        if m:
            n = max(n, int(m.group(1)))
    return preprocess_root / f"v{n + 1}"


def list_versions(preprocess_root: Path) -> list[Path]:
    if not preprocess_root.exists():
        return []
    versions: list[tuple[int, Path]] = []
    for child in preprocess_root.iterdir():
        if not child.is_dir():
            continue
        m = VERSION_RE.match(child.name)
        if m:
            versions.append((int(m.group(1)), child))
    return [p for _, p in sorted(versions)]


def read_meta(version_dir: Path) -> PreprocessMeta | None:
    path = version_dir / META_FILENAME
    if not path.exists():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return None
    return PreprocessMeta.from_dict(data)


def write_meta(version_dir: Path, meta: PreprocessMeta) -> None:
    version_dir.mkdir(parents=True, exist_ok=True)
    path = version_dir / META_FILENAME
    path.write_text(yaml.safe_dump(meta.to_dict(), sort_keys=False), encoding="utf-8")
