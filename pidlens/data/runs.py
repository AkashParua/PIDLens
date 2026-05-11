"""Training-run registry: each run is a directory under <workspace>/runs/."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml

from pidlens.data.workspace import Workspace


@dataclass
class RunRecord:
    run_id: str
    workspace_root: Path
    config: dict = field(default_factory=dict)
    summary: dict = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)
    weights: Path | None = None

    @property
    def root(self) -> Path:
        return self.workspace_root / "runs" / self.run_id

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "config": self.config,
            "summary": self.summary,
            "history": self.history,
            "weights": str(self.weights) if self.weights else None,
        }


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("run-%Y%m%d-%H%M%S")


def write_run(record: RunRecord) -> None:
    root = record.root
    root.mkdir(parents=True, exist_ok=True)
    (root / "config.yaml").write_text(yaml.safe_dump(record.config, sort_keys=False), encoding="utf-8")
    (root / "summary.json").write_text(json.dumps(record.summary, indent=2), encoding="utf-8")
    (root / "history.json").write_text(json.dumps(record.history, indent=2), encoding="utf-8")


def list_runs(workspace: Workspace) -> list[RunRecord]:
    base = workspace.runs_dir
    if not base.exists():
        return []
    records: list[RunRecord] = []
    for d in sorted(base.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        rec = _load_record(d, workspace.root)
        if rec is not None:
            records.append(rec)
    return records


def _load_record(run_dir: Path, workspace_root: Path) -> RunRecord | None:
    cfg_path = run_dir / "config.yaml"
    summary_path = run_dir / "summary.json"
    history_path = run_dir / "history.json"
    if not cfg_path.exists():
        return None
    try:
        config = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        config = {}
    summary = {}
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            summary = {}
    history: list[dict] = []
    if history_path.exists():
        try:
            history = json.loads(history_path.read_text(encoding="utf-8"))
            if not isinstance(history, list):
                history = []
        except json.JSONDecodeError:
            history = []
    weights = run_dir / "weights" / "best.pt"
    return RunRecord(
        run_id=run_dir.name,
        workspace_root=workspace_root,
        config=config,
        summary=summary,
        history=history,
        weights=weights if weights.exists() else None,
    )


def register_model(workspace: Workspace, run: RunRecord, alias: str) -> Path:
    """Copy a run's best weights into the workspace `models/` registry."""
    if run.weights is None or not run.weights.exists():
        raise FileNotFoundError("run has no weights to register")
    out_dir = workspace.models_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{alias}.pt"
    shutil.copy2(run.weights, target)
    return target
