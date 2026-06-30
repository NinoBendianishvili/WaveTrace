from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout


class AppTitle(QWidget):
    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        logo = QLabel()
        logo.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        logo_path = (
            Path(__file__).resolve().parents[2]
            / "resources"
            / "images"
            / "wavetrace_logo.png"
        )

        pixmap = QPixmap(str(logo_path))
        pixmap = pixmap.scaledToHeight(44, Qt.SmoothTransformation)

        logo.setPixmap(pixmap)

        layout.addWidget(logo)
        layout.addStretch()