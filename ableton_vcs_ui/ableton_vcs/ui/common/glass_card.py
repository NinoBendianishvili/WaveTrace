from PySide6.QtWidgets import QFrame
from ableton_vcs.config.theme import *

class GlassCard(QFrame):
    def __init__(self, radius=24, border_color=BORDER, bg_color=BG_PANEL):
        super().__init__()
        self.setObjectName("glassCard")
        self.setStyleSheet(
            f"""
            QFrame#glassCard {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: {radius}px;
            }}
            """
        )
