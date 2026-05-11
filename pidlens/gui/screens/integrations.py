"""Screen 9 — Integrations (wireframe V3: minimal list grouped by kind).

Each row is a provider. Click [Configure] to open a small per-provider form
dialog driven by the provider's `ProviderSpec.fields`. Configs are stored in
the workspace under `integrations.yaml`.
"""

from __future__ import annotations

import yaml
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from pidlens.data.workspace import Workspace
from pidlens.gui.components.widgets import Chip
from pidlens.gui.screens._base import Screen
from pidlens.ml.models.providers import (
    KIND_LABELS,
    KINDS,
    ProviderSpec,
    SettingField,
    all_provider_specs,
)


INTEGRATIONS_FILE = "integrations.yaml"


class ConfigDialog(QDialog):
    """Per-provider form. Reads the spec.fields list verbatim."""

    def __init__(self, spec: ProviderSpec, values: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Configure · {spec.label}")
        self.spec = spec
        self.values = dict(values)

        outer = QVBoxLayout(self)
        if spec.description:
            note = QLabel(spec.description)
            note.setWordWrap(True)
            note.setObjectName("muted")
            outer.addWidget(note)

        form = QFormLayout()
        self.editors: dict[str, QWidget] = {}
        for f in spec.fields:
            initial = self.values.get(f.name, f.default)
            editor = self._make_editor(f, initial)
            form.addRow(f.label, editor)
            self.editors[f.name] = editor
        outer.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def _make_editor(self, f: SettingField, initial) -> QWidget:
        if f.kind == "password":
            w = QLineEdit(str(initial or ""))
            w.setEchoMode(QLineEdit.EchoMode.Password)
            return w
        if f.kind == "int":
            w = QSpinBox()
            w.setRange(0, 2**31 - 1)
            try:
                w.setValue(int(initial))
            except (TypeError, ValueError):
                pass
            return w
        if f.kind == "float":
            w = QDoubleSpinBox()
            w.setRange(0.0, 1.0e6)
            w.setDecimals(4)
            w.setSingleStep(0.05)
            try:
                w.setValue(float(initial))
            except (TypeError, ValueError):
                pass
            return w
        if f.kind == "enum":
            from PyQt6.QtWidgets import QComboBox
            w = QComboBox()
            for opt in f.options:
                w.addItem(opt)
            idx = w.findText(str(initial))
            if idx >= 0:
                w.setCurrentIndex(idx)
            return w
        return QLineEdit(str(initial or ""))

    def collected(self) -> dict:
        out = dict(self.values)
        for name, editor in self.editors.items():
            if isinstance(editor, (QSpinBox, QDoubleSpinBox)):
                out[name] = editor.value()
            elif isinstance(editor, QLineEdit):
                out[name] = editor.text()
            else:
                from PyQt6.QtWidgets import QComboBox
                if isinstance(editor, QComboBox):
                    out[name] = editor.currentText()
        return out


class ProviderRow(QFrame):
    """One provider line: label, description, status chip, configure button."""

    def __init__(self, spec: ProviderSpec, configured: bool, on_configure, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("provider-row")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(10)

        text_col = QVBoxLayout()
        title = QLabel(spec.label)
        title.setObjectName("provider-title")
        text_col.addWidget(title)
        if spec.description:
            sub = QLabel(spec.description)
            sub.setObjectName("muted")
            sub.setWordWrap(True)
            text_col.addWidget(sub)
        lay.addLayout(text_col, 1)

        self.status = Chip("configured" if configured else "not configured",
                           kind="ok" if configured else "neutral")
        self.status.setFixedHeight(22)
        lay.addWidget(self.status)

        btn = QPushButton("Configure")
        btn.clicked.connect(lambda: on_configure(spec))
        lay.addWidget(btn)


class IntegrationsScreen(Screen):
    title = "Integrations"

    def _build(self) -> None:
        self.workspace: Workspace | None = None
        self.config: dict = {}
        self.rows: dict[str, ProviderRow] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QHBoxLayout()
        header.setContentsMargins(16, 12, 16, 0)
        h = QLabel("Integrations")
        h.setObjectName("screen-title")
        header.addWidget(h)
        header.addStretch(1)
        root.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(20)

        specs = all_provider_specs()
        for kind in KINDS:
            kind_specs = [s for s in specs if s.kind == kind]
            if not kind_specs:
                continue
            group_label = QLabel(KIND_LABELS[kind])
            group_label.setObjectName("section-head")
            outer.addWidget(group_label)
            for spec in kind_specs:
                row = ProviderRow(spec, configured=False, on_configure=self._on_configure)
                self.rows[spec.id] = row
                outer.addWidget(row)
        outer.addStretch(1)

        scroll.setWidget(container)
        root.addWidget(scroll, 1)

        self.signals.workspaceOpened.connect(self._on_workspace_opened)

    def _on_workspace_opened(self, ws: Workspace) -> None:
        self.workspace = ws
        self._load_config()
        self._refresh_statuses()

    def _config_path(self) -> Path | None:
        return self.workspace.root / INTEGRATIONS_FILE if self.workspace else None

    def _load_config(self) -> None:
        path = self._config_path()
        if not path or not path.exists():
            self.config = {}
            return
        try:
            self.config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            self.config = {}

    def _save_config(self) -> None:
        path = self._config_path()
        if not path:
            return
        path.write_text(yaml.safe_dump(self.config, sort_keys=False), encoding="utf-8")

    def _refresh_statuses(self) -> None:
        for spec in all_provider_specs():
            row = self.rows.get(spec.id)
            if row is None:
                continue
            configured = bool(self.config.get(spec.id))
            row.status.setText("configured" if configured else "not configured")
            row.status.setProperty("kind", "ok" if configured else "neutral")
            # Repolish so the property change repaints under QSS.
            row.status.style().unpolish(row.status)
            row.status.style().polish(row.status)

    def _on_configure(self, spec: ProviderSpec) -> None:
        if self.workspace is None:
            self.signals.status.emit("open a workspace first", "warn")
            return
        current = self.config.get(spec.id) or {}
        dlg = ConfigDialog(spec, current, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        self.config[spec.id] = dlg.collected()
        self._save_config()
        self._refresh_statuses()
        self.signals.status.emit(f"saved {spec.label} settings", "info")
