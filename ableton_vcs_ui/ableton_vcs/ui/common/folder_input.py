from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy
from ableton_vcs.config.theme import *

class FolderInput(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(56)
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_ELEMENT};
                border: 1px solid {BORDER};
                border-radius: 18px;
            }}
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 15px;
            }}
            """
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(12)
        self.label = QLabel(str(Path.home() / "Music/Projects/My Track"))
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        icon = QLabel("⌂")
        icon.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 18px;")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedWidth(24)
        layout.addWidget(self.label)
        layout.addWidget(icon)

    def set_path(self, path):
        self.label.setText(path)
