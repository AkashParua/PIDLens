"""Annotation canvas — QGraphicsView + scene + interactive bbox items.

Interaction model
-----------------
• click on empty canvas + drag             → draw new box (active class)
• click on box                              → select
• drag selected box                         → move
• drag a handle on selected box             → resize
• Del / Backspace                           → delete selected
• 1..9                                      → assign class N to selected
• wheel                                     → zoom around cursor
• middle-mouse drag, or Space+drag          → pan

The view emits high-level signals (selectionChanged, boxesChanged) that the
parent screen translates into autosave + attrs-panel updates. Coordinates
inside the scene are pixel-accurate against the loaded image, so converting
to/from YOLO normalised form is just `box / (img_w, img_h)`.
"""

from __future__ import annotations

import colorsys
from dataclasses import dataclass

from PyQt6.QtCore import QPoint, QPointF, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QKeyEvent, QPainter, QPen, QPixmap, QWheelEvent
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneHoverEvent,
    QGraphicsSceneMouseEvent,
    QGraphicsView,
    QWidget,
)


# ── Class palette ─────────────────────────────────────────────
def class_color(class_id: int) -> QColor:
    """Deterministic, well-spread color per class id (golden-ratio hues)."""
    if class_id < 0:
        return QColor(150, 150, 150)
    hue = (class_id * 0.6180339887) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, 0.65, 0.95)
    return QColor(int(r * 255), int(g * 255), int(b * 255))


# ── Bbox item ────────────────────────────────────────────────
HANDLE_SIZE = 8

_HANDLE_POSITIONS = (
    "tl", "t", "tr",
    "l", "r",
    "bl", "b", "br",
)


class _Handle(QGraphicsRectItem):
    """Resize grip on a BBoxItem. The parent box reads these in its mouseMove."""

    def __init__(self, role: str, parent: "BBoxItem") -> None:
        super().__init__(parent)
        self.role = role
        self.setRect(-HANDLE_SIZE / 2, -HANDLE_SIZE / 2, HANDLE_SIZE, HANDLE_SIZE)
        self.setBrush(QBrush(QColor(255, 255, 255)))
        self.setPen(QPen(QColor(40, 30, 20), 1))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, False)
        self.setAcceptHoverEvents(True)
        self.setCursor(_cursor_for_handle(role))
        self.setZValue(2)
        self.hide()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        # Let the parent BBoxItem run the resize loop.
        parent = self.parentItem()
        if isinstance(parent, BBoxItem):
            parent.begin_resize(self.role, event.scenePos())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        parent = self.parentItem()
        if isinstance(parent, BBoxItem) and parent.resizing:
            parent.do_resize(event.scenePos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        parent = self.parentItem()
        if isinstance(parent, BBoxItem) and parent.resizing:
            parent.end_resize()
            event.accept()
            return
        super().mouseReleaseEvent(event)


def _cursor_for_handle(role: str):
    c = {
        "tl": Qt.CursorShape.SizeFDiagCursor,
        "br": Qt.CursorShape.SizeFDiagCursor,
        "tr": Qt.CursorShape.SizeBDiagCursor,
        "bl": Qt.CursorShape.SizeBDiagCursor,
        "t": Qt.CursorShape.SizeVerCursor,
        "b": Qt.CursorShape.SizeVerCursor,
        "l": Qt.CursorShape.SizeHorCursor,
        "r": Qt.CursorShape.SizeHorCursor,
    }
    return c.get(role, Qt.CursorShape.ArrowCursor)


class BBoxItem(QGraphicsRectItem):
    """One labeled rectangle. Position + size are in image-pixel coordinates."""

    def __init__(self, rect: QRectF, class_id: int = 0, scene_bounds: QRectF | None = None) -> None:
        super().__init__()
        self.class_id = class_id
        self.scene_bounds = scene_bounds or QRectF()
        self._setting_rect = False
        self.resizing = False
        self._resize_role: str | None = None
        self._resize_origin: QRectF | None = None

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(1)

        # Children: resize handles.
        self.handles: dict[str, _Handle] = {role: _Handle(role, self) for role in _HANDLE_POSITIONS}

        self.set_rect(rect)
        self.apply_style()

    # ── Class / style ─────────────────────────────────────────
    def apply_style(self) -> None:
        c = class_color(self.class_id)
        fill = QColor(c)
        fill.setAlpha(60 if not self.isSelected() else 90)
        pen = QPen(c)
        pen.setWidthF(2.0 if self.isSelected() else 1.4)
        pen.setCosmetic(True)
        self.setBrush(QBrush(fill))
        self.setPen(pen)

    def set_class(self, class_id: int) -> None:
        self.class_id = max(0, int(class_id))
        self.apply_style()

    # ── Geometry helpers ──────────────────────────────────────
    def set_rect(self, rect: QRectF) -> None:
        """Normalize, clamp to bounds, and update handle positions."""
        if rect.width() < 0:
            rect = QRectF(rect.right(), rect.top(), -rect.width(), rect.height())
        if rect.height() < 0:
            rect = QRectF(rect.left(), rect.bottom(), rect.width(), -rect.height())
        if not self.scene_bounds.isNull():
            rect = rect.intersected(self.scene_bounds)
        rect = rect.normalized()
        rect.setWidth(max(rect.width(), 1.0))
        rect.setHeight(max(rect.height(), 1.0))

        # Use (0,0)-rooted geometry + setPos so QGraphicsItem move math works.
        self._setting_rect = True
        self.setPos(rect.topLeft())
        super().setRect(0, 0, rect.width(), rect.height())
        self._setting_rect = False
        self._position_handles()

    def absolute_rect(self) -> QRectF:
        """Return rect in scene-space (top-left + width/height)."""
        r = self.rect()
        return QRectF(self.pos(), QSize(int(r.width()), int(r.height())))

    def _position_handles(self) -> None:
        r = self.rect()
        cx = r.center().x()
        cy = r.center().y()
        coords = {
            "tl": (r.left(),  r.top()),
            "t":  (cx,        r.top()),
            "tr": (r.right(), r.top()),
            "l":  (r.left(),  cy),
            "r":  (r.right(), cy),
            "bl": (r.left(),  r.bottom()),
            "b":  (cx,        r.bottom()),
            "br": (r.right(), r.bottom()),
        }
        for role, (x, y) in coords.items():
            self.handles[role].setPos(x, y)

    # ── Selection visual + propagate ─────────────────────────
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            for h in self.handles.values():
                h.setVisible(bool(value))
            self.apply_style()
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and not self._setting_rect:
            # Clamp dragging so the box can't leave the image.
            if not self.scene_bounds.isNull():
                new_pos: QPointF = value
                r = self.rect()
                max_x = self.scene_bounds.right() - r.width()
                max_y = self.scene_bounds.bottom() - r.height()
                x = max(self.scene_bounds.left(), min(new_pos.x(), max_x))
                y = max(self.scene_bounds.top(), min(new_pos.y(), max_y))
                if x != new_pos.x() or y != new_pos.y():
                    return QPointF(x, y)
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            scene = self.scene()
            if isinstance(scene, CanvasScene):
                scene._emit_changed()
        return super().itemChange(change, value)

    # ── Resize via handles ────────────────────────────────────
    def begin_resize(self, role: str, scene_pt: QPointF) -> None:
        self.resizing = True
        self._resize_role = role
        self._resize_origin = self.absolute_rect()

    def do_resize(self, scene_pt: QPointF) -> None:
        if not self.resizing or not self._resize_origin or not self._resize_role:
            return
        r = QRectF(self._resize_origin)
        role = self._resize_role
        if "l" in role: r.setLeft(scene_pt.x())
        if "r" in role: r.setRight(scene_pt.x())
        if "t" in role: r.setTop(scene_pt.y())
        if "b" in role: r.setBottom(scene_pt.y())
        self.set_rect(r)
        scene = self.scene()
        if isinstance(scene, CanvasScene):
            scene._emit_changed()

    def end_resize(self) -> None:
        self.resizing = False
        self._resize_role = None
        self._resize_origin = None


# ── Scene ────────────────────────────────────────────────────
@dataclass
class BoxData:
    """Serialisable form of a box for the screen layer."""
    class_id: int
    x1: float
    y1: float
    x2: float
    y2: float


class CanvasScene(QGraphicsScene):
    """Holds the image pixmap + bbox items; emits when the user changes anything."""

    boxesChanged = pyqtSignal()        # any geometry or class change committed
    selectionChangedTo = pyqtSignal(object)  # BBoxItem | None

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.image_item: QGraphicsPixmapItem | None = None
        self.image_size = QSize(0, 0)
        self.active_class_id = 0
        self._pending_box: BBoxItem | None = None
        self._draw_origin: QPointF | None = None
        self._suspend_emit = False
        self.selectionChanged.connect(self._on_selection_changed)

    # ── Image ─────────────────────────────────────────────────
    def set_image(self, pixmap: QPixmap | None) -> None:
        self.clear_boxes()
        if self.image_item is not None:
            self.removeItem(self.image_item)
            self.image_item = None
        if pixmap is None or pixmap.isNull():
            self.image_size = QSize(0, 0)
            self.setSceneRect(QRectF(0, 0, 1, 1))
            return
        self.image_item = QGraphicsPixmapItem(pixmap)
        self.image_item.setZValue(-1)
        self.addItem(self.image_item)
        self.image_size = pixmap.size()
        self.setSceneRect(QRectF(0, 0, pixmap.width(), pixmap.height()))

    # ── Box ops ───────────────────────────────────────────────
    def add_box(self, x1: float, y1: float, x2: float, y2: float, class_id: int) -> BBoxItem:
        bounds = self.sceneRect()
        item = BBoxItem(QRectF(QPointF(x1, y1), QPointF(x2, y2)), class_id, bounds)
        self.addItem(item)
        self._emit_changed()
        return item

    def clear_boxes(self) -> None:
        for item in list(self.items()):
            if isinstance(item, BBoxItem):
                self.removeItem(item)

    def export_boxes(self) -> list[BoxData]:
        out: list[BoxData] = []
        for item in self.items():
            if isinstance(item, BBoxItem):
                r = item.absolute_rect()
                out.append(BoxData(item.class_id, r.left(), r.top(), r.right(), r.bottom()))
        return out

    # ── Mouse: new-box draw ───────────────────────────────────
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.image_item is not None:
            item = self.itemAt(event.scenePos(), self.views()[0].transform()) if self.views() else None
            if isinstance(item, (BBoxItem, _Handle)):
                super().mousePressEvent(event)
                return
            # Start drawing a new box.
            self._draw_origin = event.scenePos()
            self._pending_box = self.add_box(
                self._draw_origin.x(), self._draw_origin.y(),
                self._draw_origin.x() + 1, self._draw_origin.y() + 1,
                self.active_class_id,
            )
            self._pending_box.setSelected(True)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._pending_box is not None and self._draw_origin is not None:
            r = QRectF(self._draw_origin, event.scenePos()).normalized()
            self._pending_box.set_rect(r)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._pending_box is not None:
            r = self._pending_box.absolute_rect()
            if r.width() < 3 or r.height() < 3:
                self.removeItem(self._pending_box)
            self._pending_box = None
            self._draw_origin = None
            self._emit_changed()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    # ── Selection / change propagation ───────────────────────
    def _on_selection_changed(self) -> None:
        sel = [i for i in self.selectedItems() if isinstance(i, BBoxItem)]
        self.selectionChangedTo.emit(sel[0] if sel else None)

    def _emit_changed(self) -> None:
        if not self._suspend_emit:
            self.boxesChanged.emit()


# ── View ─────────────────────────────────────────────────────
class AnnotationCanvas(QGraphicsView):
    """Pan / zoom wrapper around a CanvasScene."""

    classRequested = pyqtSignal(int)
    deleteRequested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene = CanvasScene(self)
        self.setScene(self._scene)
        self.setObjectName("annotation-canvas")
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setBackgroundBrush(QBrush(QColor("#cfc8bd")))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setMouseTracking(True)
        self._pan_active = False
        self._pan_last: QPoint | None = None
        self._space_held = False

    @property
    def canvas_scene(self) -> CanvasScene:
        return self._scene

    def fit_to_view(self) -> None:
        if self._scene.image_item is None:
            return
        self.resetTransform()
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    # ── Zoom ──────────────────────────────────────────────────
    def wheelEvent(self, event: QWheelEvent) -> None:
        if self._scene.image_item is None:
            return
        delta = event.angleDelta().y()
        factor = 1.15 if delta > 0 else 1 / 1.15
        # Zoom around cursor.
        pre = self.mapToScene(event.position().toPoint())
        self.scale(factor, factor)
        post = self.mapToScene(event.position().toPoint())
        diff = post - pre
        self.translate(diff.x(), diff.y())

    # ── Pan ───────────────────────────────────────────────────
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space_held = True
            self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.deleteRequested.emit()
            event.accept()
            return
        if Qt.Key.Key_1 <= event.key() <= Qt.Key.Key_9:
            self.classRequested.emit(event.key() - Qt.Key.Key_1)
            event.accept()
            return
        if event.key() == Qt.Key.Key_F:
            self.fit_to_view()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape:
            self._scene.clearSelection()
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space_held = False
            self.viewport().unsetCursor()
            event.accept()
            return
        super().keyReleaseEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton or (
            event.button() == Qt.MouseButton.LeftButton and self._space_held
        ):
            self._pan_active = True
            self._pan_last = event.position().toPoint()
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._pan_active and self._pan_last is not None:
            curr = event.position().toPoint()
            delta = curr - self._pan_last
            self._pan_last = curr
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._pan_active:
            self._pan_active = False
            self._pan_last = None
            self.viewport().setCursor(
                Qt.CursorShape.OpenHandCursor if self._space_held else Qt.CursorShape.ArrowCursor
            )
            event.accept()
            return
        super().mouseReleaseEvent(event)
