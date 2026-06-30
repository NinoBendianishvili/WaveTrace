from PySide6.QtWidgets import QVBoxLayout

from ableton_vcs.config.theme import *
from ableton_vcs.ui.common.glass_card import GlassCard
from ableton_vcs.ui.graph.commit_graph_view import CommitGraphView


class GraphPanel(GlassCard):
    def __init__(self, repository):
        super().__init__(radius=26, border_color=BORDER, bg_color=BG_PANEL)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(22, 18, 22, 22)
        self.layout.setSpacing(16)

        self.graph = CommitGraphView(repository)
        self.layout.addWidget(self.graph)

    def set_repository(self, repository):
        self.graph.set_repository(repository)

    def set_pending_changes(self, has_pending_changes):
        self.graph.set_pending_changes(has_pending_changes)