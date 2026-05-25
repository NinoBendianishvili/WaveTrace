from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from ableton_vcs.config.theme import *

class InfoRow(QWidget):
    def __init__(self, icon_text, title):
        super().__init__()
        self.value_label = QLabel("")
        self.value_label.setWordWrap(True)
        self.value_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px; font-weight: 600;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(10)
        icon = QLabel(icon_text)
        icon.setFixedWidth(28)
        icon.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        icon.setStyleSheet(f"color: {ACCENT}; font-size: 18px;")
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; font-weight: 500;")
        top.addWidget(icon)
        top.addWidget(title_label)
        top.addStretch()
        value_wrap = QHBoxLayout()
        value_wrap.setContentsMargins(38, 0, 0, 0)
        value_wrap.addWidget(self.value_label)
        layout.addLayout(top)
        layout.addLayout(value_wrap)

    def set_value(self, value):
        self.value_label.setText(value)
