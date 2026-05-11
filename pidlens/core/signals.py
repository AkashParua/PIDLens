"""Centralized signal bus.

Screens never reach across the tree to talk to each other; they emit on this
shared object instead. MainWindow owns the single instance and hands it to
every screen at construction time.
"""

from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal


class AppSignals(QObject):
    # ── Workspace
    # emits Workspace; typed as object because pyqtSignal needs the class
    # at import time and we want to keep this module dependency-free.
    workspaceOpened = pyqtSignal(object)
    workspaceRescanned = pyqtSignal(object)

    # ── Cross-screen navigation. Screens emit a short key ("annot", "train"…)
    # that MainWindow translates into a stack switch.
    requestScreen = pyqtSignal(str)

    # ── Selection. The currently-focused image path; consumed by Triage and
    # Annotation screens.
    imageSelected = pyqtSignal(object)  # Path | None

    # ── Annotations changed for a given image path. Emit after autosave so
    # other screens (Triage badge counts) update in place.
    annotationsChanged = pyqtSignal(object)  # Path

    # ── Preprocessing. Emitted when a new versioned preprocess dir is written.
    preprocessVersionCreated = pyqtSignal(object)  # Path to the version dir

    # ── Training. emit (run_id, epoch, metrics_dict).
    trainingTick = pyqtSignal(str, int, dict)
    trainingFinished = pyqtSignal(str, dict)  # run_id, final_metrics

    # ── Toast / status messages. Severity ∈ {"info", "warn", "error"}.
    status = pyqtSignal(str, str)  # text, severity
