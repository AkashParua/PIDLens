"""Primary QMainWindow. Sidebar nav + stacked screen pages."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from pidlens.config import APP_NAME, STYLES_DIR
from pidlens.core.signals import AppSignals
from pidlens.data.workspace import Workspace
from pidlens.gui.screens import (
    AnnotationScreen,
    AugmentScreen,
    IntegrationsScreen,
    ModelsScreen,
    ParseScreen,
    PreprocessScreen,
    SplitScreen,
    TrainingScreen,
    TriageScreen,
)

# Order matches the README feature flow and the wireframe sections.
SCREENS: list[tuple[str, str, type[QWidget]]] = [
    ("parse", "1 · Parse", ParseScreen),
    ("triage", "2 · Triage", TriageScreen),
    ("annot", "3 · Annotate", AnnotationScreen),
    ("pre", "4 · Preprocess", PreprocessScreen),
    ("aug", "5 · Augment", AugmentScreen),
    ("split", "6 · Split", SplitScreen),
    ("train", "7 · Training", TrainingScreen),
    ("models", "8 · Models", ModelsScreen),
    ("integ", "9 · Integrations", IntegrationsScreen),
]


class Sidebar(QListWidget):
    """Left rail. Width fixed so the canvas takes the rest."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(180)
        self.setSpacing(2)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for key, label, _ in SCREENS:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.addItem(item)


class MainWindow(QMainWindow):
    workspaceChanged = pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1400, 900)

        self.signals = AppSignals()
        self.workspace: Workspace | None = None

        self._build_ui()
        self._build_menu()
        self._load_styles()
        self._wire()

        self.sidebar.setCurrentRow(0)

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.stack = QStackedWidget()
        self.stack.setObjectName("screen-stack")

        self.screens: dict[str, QWidget] = {}
        for key, _, cls in SCREENS:
            widget = cls(signals=self.signals)
            self.screens[key] = widget
            self.stack.addWidget(widget)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        status = QStatusBar()
        self.workspace_label = QLabel("no workspace")
        self.workspace_label.setObjectName("status-workspace")
        status.addWidget(self.workspace_label)
        self.setStatusBar(status)

    def _build_menu(self) -> None:
        bar = self.menuBar()
        file_menu = bar.addMenu("&File")

        open_action = QAction("Open Workspace…", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.on_open_workspace)
        file_menu.addAction(open_action)

        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

    def _load_styles(self) -> None:
        qss_path = STYLES_DIR / "app.qss"
        if qss_path.exists():
            self.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    def _wire(self) -> None:
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.signals.workspaceOpened.connect(self._on_workspace_opened)
        self.signals.requestScreen.connect(self._goto_screen)

    # ──────────────────────────────────────────────────────────
    # actions
    # ──────────────────────────────────────────────────────────
    def on_open_workspace(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Open Workspace", str(Path.home()))
        if directory:
            ws = Workspace(Path(directory))
            ws.scan()
            self.signals.workspaceOpened.emit(ws)

    def _on_workspace_opened(self, ws: Workspace) -> None:
        self.workspace = ws
        self.workspace_label.setText(str(ws.root))

    def _goto_screen(self, key: str) -> None:
        for i, (k, _, _) in enumerate(SCREENS):
            if k == key:
                self.sidebar.setCurrentRow(i)
                return
