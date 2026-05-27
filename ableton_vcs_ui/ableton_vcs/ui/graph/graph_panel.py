from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout

from ableton_vcs.config.theme import *
from ableton_vcs.ui.common.glass_card import GlassCard
from ableton_vcs.ui.graph.commit_graph_view import CommitGraphView


class BranchBadge(QLabel):
    def __init__(self, text):
        super().__init__(text)

        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(30)
        self.setFixedWidth(64)
        self.setStyleSheet(
            f"""
            QLabel {{
                background-color: {BG_ELEMENT};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 10px;
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 0.6px;
            }}
            """
        )


class GraphPanel(GlassCard):
    def __init__(self, repository):
        super().__init__(radius=26, border_color=BORDER, bg_color=BG_PANEL)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(22, 18, 22, 22)
        self.layout.setSpacing(16)

        self.badge = BranchBadge(repository.branch_label)
        self.layout.addWidget(self.badge, 0, Qt.AlignLeft)

        self.graph = CommitGraphView(repository)
        self.layout.addWidget(self.graph)

    def set_repository(self, repository):
        self.badge.setText(repository.branch_label)
        self.graph.set_repository(repository)

    def set_pending_changes(self, has_pending_changes):
        self.graph.set_pending_changes(has_pending_changes)