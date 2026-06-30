from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPen, QBrush
from PySide6.QtWidgets import QGraphicsEllipseItem

class CommitNodeItem(QGraphicsEllipseItem):
    def __init__(self, commit_data, radius, border_color, fill_color, on_click):
        self.commit_data = commit_data
        self.on_click = on_click
        super().__init__(QRectF(-radius, -radius, radius * 2, radius * 2))
        self.setPen(QPen(QColor(border_color), 2.4))
        self.setBrush(QBrush(QColor(fill_color)))
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        self.on_click(self.commit_data["hash"])
        super().mousePressEvent(event)

    def hoverEnterEvent(self, event):
        self.setScale(1.08)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setScale(1.0)
        super().hoverLeaveEvent(event)
