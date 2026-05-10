# PIDLens
Annotation tool specially designed for annotating PFDs and PIDs for AutoQRA

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
│   │   │   ├── rt_detr.py
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
