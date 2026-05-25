from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel
from ableton_vcs.config.theme import *

class MergeTrackRow(QFrame):
    toggled = Signal(str, bool)

    def __init__(self, side_name, group_name, track_name, status, selected=False):
        super().__init__()
        self.side_name = side_name
        self.group_name = group_name
        self.track_name = track_name
        self.status = status
        self.setStyleSheet(f"QFrame {{ background-color: {BG_ELEMENT}; border: 1px solid {BORDER}; border-radius: 12px; }}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(selected)
        self.checkbox.setCursor(Qt.PointingHandCursor)
        self.checkbox.setStyleSheet(
            f"""
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #8A8A8A;
                background: {BG_PANEL};
            }}
            QCheckBox::indicator:checked {{
                background: {TEXT_PRIMARY};
                border: 2px solid {TEXT_PRIMARY};
            }}
            """
        )
        color_map = {"unchanged": GREEN, "new": ORANGE, "collision": RED}
        label = QLabel(track_name)
        label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 600; background: transparent; border: none;")
        status_chip = QLabel(status)
        status_chip.setAlignment(Qt.AlignCenter)
        status_chip.setFixedWidth(86)
        status_chip.setStyleSheet(f"background-color: transparent; color: {color_map[status]}; border: none; font-size: 11px; font-weight: 700; padding: 5px 8px;")
        layout.addWidget(self.checkbox)
        layout.addWidget(label, 1)
        layout.addWidget(status_chip)
        self.checkbox.toggled.connect(self.emit_toggle)

    def emit_toggle(self, checked):
        self.toggled.emit(f"{self.side_name}:{self.group_name}:{self.track_name}", checked)

    def set_checked_silently(self, checked):
        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(checked)
        self.checkbox.blockSignals(False)
