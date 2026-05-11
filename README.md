# PIDLens
Fast natively running annotation tool.

## Install & Run

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .
python main.py
```

On WSL you need either WSLg (Windows 11) or an X server (VcXsrv/X410) to see the window.

The ML extras (`rfdetr`, `torch`) are optional. The Training screen ships with a mock loop that emits realistic-looking metrics so the rest of the app can be exercised end-to-end without ML deps. To install them:

```bash
pip install -e '.[ml]'
```

## Status

| Screen | Wireframe variant | Status |
|---|---|---|
| 1. Parse landing | V2 (file tree + parse preview) | working |
| 2. Image triage | V1 (status-badge grid) | working |
| 3. Annotation canvas | V1 (classes/canvas/attrs + thumbstrip) | working — bbox draw/move/resize/delete, autosave to YOLOv8 |
| 4. Preprocessing pipeline | V3 (in/out preview per card) | working — versioned dirs + meta.yaml |
| 5. Augmentation | V3 (3-col card grid) | working — saves to `augment.yaml` |
| 6. Train/val/test split | V3 (donut + per-class bars) | working — stratified, writes train/val/test.txt |
| 7. Training loop | V2 (KPIs · 2 charts · terminal) | **mock training**; real rf-detr call is one method swap (see `core/workers/ml_worker.py`) |
| 8. Models / runs | V1 (runs table + detail) | working — reads `runs/`, registers weights into `models/` |
| 9. Integrations | V3 (list grouped by kind) | shell only — providers raise `NotImplementedError`; configs persist to `integrations.yaml` |

Known stubs to flesh out before production use:
- `core/workers/ml_worker.py::TrainTask._mock_train` — replace with `rfdetr` invocation.
- `ml/models/providers.py` — concrete `infer()` for each provider.
- Workspace watcher is plumbed (`data/watcher.py`) but not yet wired into MainWindow's auto-rescan.

## Features 
- Everything runs locally, directory based, no upload/download, minimizing latency.
- Standard 2D annotation of PFDs and PIDs using bounding boxes.
- Ability to perform pre-processing- thresholding, morphological operations, fillups, resizing etc.
    - Ability to apply transformations both locally in a box and globally.
    - Ability to preview and save the results of such morphological operations in versioned directories.
    - Metdata (a .yaml file) records the sequence and values related to morphological operations.
    - Original images are always untouched.
- Annotations are always generated in yolov8 format.
- Ability to split in test-train-validation.
- Integrated rf-detr training loop.
- Interfaces available for integrating various VLMs, Object detection models, OCR models.
- Storing, versioning and evaluating said models.
- Super fast and ligthweight interface.
- Load and detect already annotated images, identifies un-annotated images, visualizes annotation.
- Ability to implement custom pre-processing using scripts and keep a record.
- Ability to implement curstom Augmentations

## Directory Structure

```shell
pidlens_project/
├── .gitignore
├── pyproject.toml              # Dependency management (recommended over requirements.txt)
├── README.md
├── main.py                     # Entry point: initializes QApplication and Main Window
│
├── pidlens/                    # Main application package
│   ├── __init__.py
│   ├── config.py               # Global settings, singleton configs, default paths
│   │
│   ├── gui/                    # Pure UI Layer (Main Thread only)
│   │   ├── __init__.py
│   │   ├── main_window.py      # The primary QMainWindow
│   │   ├── canvas.py           # Custom QGraphicsView/QGraphicsScene for rendering
│   │   ├── components/         # Reusable UI parts (e.g., Sliders, sidebars, toolbars)
│   │   └── dialogs/            # Popups (e.g., "Export Dataset", "Settings")
│   │
│   ├── core/                   # Business Logic & Multithreading
│   │   ├── __init__.py
│   │   ├── workers/            # QRunnable/QThread classes (Never block the UI)
│   │   │   ├── vision_worker.py  # OpenCV operations
│   │   │   ├── ml_worker.py      # Inference loops
│   │   │   └── io_worker.py      # File saving/loading
│   │   ├── signals.py          # Centralized signal/slot definitions
│   │   └── utils.py            # Helper functions (e.g., array_to_qimage)
│   │
│   ├── ml/                     # Machine Learning & Vision Pipelines
│   │   ├── __init__.py
│   │   ├── models/             # Model architectures and Singleton loaders
│   │   │   ├── rf_detr.py
│   │   │   └── ocr_engine.py
│   │   ├── vision/             # Image processing logic
│   │   │   └── morphology.py   # OpenCV / CUDA transformations
│   │   └── weights/            # Local model weights (usually gitignored)
│   │
│   ├── data/                   # File System & Workspace Management
│   │   ├── __init__.py
│   │   ├── workspace.py        # Logic for monitoring the target directory
│   │   ├── yolo_parser.py      # Reads/writes YOLOv8 format TXT files
│   │   └── yaml_manager.py     # Reads/writes the versioned metadata
│   │
│   └── assets/                 # Static files
│       ├── icons/              # UI icons (.png, .svg)
│       └── styles/             # Qt Style Sheets (.qss)
│
└── tests/                      # Unit tests (pytest)
    ├── test_vision.py
    └── test_yolo_parser.py
```
