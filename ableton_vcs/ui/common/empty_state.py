from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from ableton_vcs.ui.common.pill_button import PillButton

class EmptyStateWidget(QWidget):
    def __init__(self, text, with_button=False, button_text=""):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        layout.addStretch()
        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setMinimumHeight(90)
        self.label.setMaximumWidth(760)
        self.label.setStyleSheet("color: #8C8C8C; background: transparent;")
        label_font = QFont("Arial", 24)
        label_font.setWeight(QFont.Medium)
        self.label.setFont(label_font)
        layout.addWidget(self.label, 0, Qt.AlignHCenter)
        self.button = PillButton(button_text, primary=True) if with_button else None
        if self.button is not None:
            layout.addWidget(self.button, 0, Qt.AlignHCenter)
        layout.addStretch()
