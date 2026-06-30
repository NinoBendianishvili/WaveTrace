from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton
from ableton_vcs.config.theme import *

class PillButton(QPushButton):
    def __init__(self, text, primary=False, compact=False):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(44 if compact else 54)
        self.setMinimumWidth(112 if compact else 150)
        self.normal_style = f"""
            QPushButton {{
                background-color: {BG_ELEMENT};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 16px;
                font-size: 14px;
                font-weight: 600;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: {BG_ELEMENT_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {BORDER};
            }}
        """
        self.primary_style = f"""
            QPushButton {{
                color: #111111;
                border: 1px solid {ACCENT};
                border-radius: 16px;
                font-size: 14px;
                font-weight: 700;
                padding: 0 22px;
                background-color: {ACCENT};
            }}
            QPushButton:hover {{
                background-color: #ffb347;
            }}
            QPushButton:pressed {{
                background-color: #cc7a00;
            }}
        """
        self.disabled_primary_style = f"""
            QPushButton {{
                background-color: #5b5b5b;
                color: #cfcfcf;
                border: 1px solid #5b5b5b;
                border-radius: 16px;
                font-size: 14px;
                font-weight: 700;
                padding: 0 22px;
            }}
        """
        self.setStyleSheet(self.primary_style if primary else self.normal_style)

    def set_primary_enabled(self, enabled):
        self.setEnabled(enabled)
        self.setStyleSheet(self.primary_style if enabled else self.disabled_primary_style)
