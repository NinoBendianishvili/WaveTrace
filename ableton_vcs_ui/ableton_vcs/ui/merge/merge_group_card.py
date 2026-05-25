from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QVBoxLayout
from ableton_vcs.config.theme import *
from ableton_vcs.ui.common.glass_card import GlassCard
from ableton_vcs.ui.merge.merge_track_row import MergeTrackRow

class MergeGroupCard(GlassCard):
    selection_changed = Signal(str, bool)

    def __init__(self, side_name, group_data):
        super().__init__(radius=18, border_color=BORDER, bg_color=BG_PANEL)
        self.side_name = side_name
        self.group_name = group_data["group"]
        self.rows = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        self.group_checkbox = QCheckBox()
        self.group_checkbox.setCursor(Qt.PointingHandCursor)
        self.group_checkbox.setStyleSheet(
            f"""
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 10px;
                border: 2px solid #8A8A8A;
                background: {BG_PANEL};
            }}
            QCheckBox::indicator:checked {{
                background: {TEXT_PRIMARY};
                border: 2px solid {TEXT_PRIMARY};
            }}
            """
        )
        title = QLabel(self.group_name)
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 700; background: transparent; border: none;")
        count = QLabel(f"{len(group_data['tracks'])} tracks")
        count.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px; background: transparent; border: none;")
        top.addWidget(self.group_checkbox)
        top.addWidget(title)
        top.addStretch()
        top.addWidget(count)
        layout.addLayout(top)
        for track in group_data["tracks"]:
            selected = track["status"] == "unchanged"
            row = MergeTrackRow(side_name, self.group_name, track["name"], track["status"], selected)
            row.toggled.connect(self.on_row_toggled)
            self.rows.append(row)
            layout.addWidget(row)
        self.group_checkbox.toggled.connect(self.on_group_toggled)
        self.sync_group_checkbox()

    def on_group_toggled(self, checked):
        for row in self.rows:
            row.set_checked_silently(checked)
            self.selection_changed.emit(f"{self.side_name}:{self.group_name}:{row.track_name}", checked)

    def on_row_toggled(self, key, checked):
        self.selection_changed.emit(key, checked)
        self.sync_group_checkbox()

    def sync_group_checkbox(self):
        all_checked = all(row.checkbox.isChecked() for row in self.rows)
        self.group_checkbox.blockSignals(True)
        self.group_checkbox.setChecked(all_checked)
        self.group_checkbox.blockSignals(False)
