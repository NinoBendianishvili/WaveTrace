from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget
from ableton_vcs.config.theme import *
from ableton_vcs.ui.common.glass_card import GlassCard
from ableton_vcs.ui.merge.merge_group_card import MergeGroupCard

class MergeSidePanel(GlassCard):
    selection_changed = Signal(str, bool)

    def __init__(self, side_name, commit_name, groups_data):
        super().__init__(radius=24, border_color=BORDER, bg_color=BG_PANEL)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)
        title_row = QHBoxLayout()
        title = QLabel(side_name)
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 20px; font-weight: 700;")
        subtitle = QLabel(commit_name)
        subtitle.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        subtitle.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(subtitle)
        layout.addLayout(title_row)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background: transparent; border: none; }} QScrollBar:vertical {{ background: {BG_PANEL}; width: 10px; }} QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; }}")
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)
        for group in groups_data:
            card = MergeGroupCard(side_name, group)
            card.selection_changed.connect(self.selection_changed.emit)
            content_layout.addWidget(card)
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
