from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ableton_vcs.config.theme import *


class WaveformWidget(QWidget):
    seek_requested = Signal(float)

    def __init__(self):
        super().__init__()

        self.progress = 0.0
        self.enabled_for_seek = False

        self.setMinimumHeight(48)
        self.setMaximumHeight(56)
        self.setCursor(Qt.ArrowCursor)

    def set_progress(self, progress):
        self.progress = max(0.0, min(1.0, progress))
        self.update()

    def set_seek_enabled(self, enabled):
        self.enabled_for_seek = enabled
        self.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)
        self.update()

    def mousePressEvent(self, event):
        if not self.enabled_for_seek:
            return

        if event.button() == Qt.LeftButton:
            self.seek_from_x(event.position().x())

    def mouseMoveEvent(self, event):
        if not self.enabled_for_seek:
            return

        if event.buttons() & Qt.LeftButton:
            self.seek_from_x(event.position().x())

    def seek_from_x(self, x):
        width = max(self.width(), 1)
        progress = max(0.0, min(1.0, x / width))

        self.set_progress(progress)
        self.seek_requested.emit(progress)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        if width <= 0 or height <= 0:
            return

        center_y = height / 2
        bar_count = max(34, int(width / 11))
        spacing = width / bar_count
        progress_x = width * self.progress

        for index in range(bar_count):
            x = index * spacing + spacing / 2
            bar_height = self.bar_height(index, height)

            if self.enabled_for_seek:
                color = QColor(ACCENT if x <= progress_x else TEXT_SECONDARY)
            else:
                color = QColor(TEXT_SECONDARY)
                color.setAlpha(90)

            pen_width = max(2, int(spacing * 0.28))

            pen = QPen(color, pen_width)
            pen.setCapStyle(Qt.RoundCap)

            painter.setPen(pen)
            painter.drawLine(
                int(x),
                int(center_y - bar_height / 2),
                int(x),
                int(center_y + bar_height / 2)
            )

        if self.enabled_for_seek:
            self.draw_progress_handle(painter, progress_x, height)

    def draw_progress_handle(self, painter, progress_x, height):
        pen = QPen(QColor(ACCENT), 2)
        pen.setCapStyle(Qt.RoundCap)

        painter.setPen(pen)
        painter.drawLine(
            int(progress_x),
            7,
            int(progress_x),
            height - 7
        )

    def bar_height(self, index, height):
        pattern = [
            12, 18, 24, 15, 30, 22, 34, 17,
            26, 36, 20, 31, 38, 23, 33, 16,
            27, 35, 21, 30, 19, 28, 34, 18,
            25, 32, 20, 29, 15, 27, 36, 19,
            24, 31,
        ]

        value = pattern[index % len(pattern)]

        return min(value, height - 10)