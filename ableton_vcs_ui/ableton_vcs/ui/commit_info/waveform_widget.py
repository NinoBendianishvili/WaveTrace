from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from ableton_vcs.config.theme import *

class WaveformWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(70)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(TEXT_SECONDARY), 4)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        bars = [18, 30, 22, 42, 26, 34, 48, 24, 18, 26, 40, 56, 28, 20, 33, 25, 38, 21, 44, 29, 31, 24, 36, 46, 27, 35, 41, 22, 39, 30, 18, 21, 34, 29]
        bar_width = max(4, self.width() // (len(bars) * 2))
        gap = bar_width
        x = 8
        center = self.height() / 2
        for height in bars:
            painter.drawLine(x, center - height / 2, x, center + height / 2)
            x += bar_width + gap
