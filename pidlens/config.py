"""Global settings, paths, and default values."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

APP_NAME = "PIDLens"
ORG_NAME = "PIDLens"

PACKAGE_ROOT = Path(__file__).resolve().parent
ASSETS_DIR = PACKAGE_ROOT / "assets"
STYLES_DIR = ASSETS_DIR / "styles"
ICONS_DIR = ASSETS_DIR / "icons"
WEIGHTS_DIR = PACKAGE_ROOT / "ml" / "weights"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

# Per-workspace folder layout. Subdirectories are created lazily on first write.
WORKSPACE_IMAGES_DIR = "images"
WORKSPACE_LABELS_DIR = "labels"
WORKSPACE_DATA_YAML = "data.yaml"
WORKSPACE_PREPROCESS_DIR = "preprocess"
WORKSPACE_RUNS_DIR = "runs"
WORKSPACE_MODELS_DIR = "models"


@dataclass
class Settings:
    """Mutable runtime settings. One instance shared via get_settings()."""

    recent_dirs: list[Path] = field(default_factory=list)
    last_class_names: list[str] = field(default_factory=list)
    thumbnail_size: int = 96
    watch_workspace: bool = True
    autosave_labels: bool = True


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
