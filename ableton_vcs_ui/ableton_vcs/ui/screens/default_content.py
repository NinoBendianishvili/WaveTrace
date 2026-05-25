from PySide6.QtWidgets import QFrame, QHBoxLayout, QWidget
from ableton_vcs.config.theme import *
from ableton_vcs.ui.graph.graph_panel import GraphPanel
from ableton_vcs.ui.commit_info.commit_info_panel import CommitInfoPanel

class DefaultContent(QWidget):
    def __init__(self, repository):
        super().__init__()
        content_layout = QHBoxLayout(self)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        self.graph_panel = GraphPanel(repository)
        self.info_panel = CommitInfoPanel()
        self.info_panel.setFixedWidth(500)
        content_layout.addWidget(self.graph_panel, 1)
        vertical_divider = QFrame()
        vertical_divider.setFrameShape(QFrame.VLine)
        vertical_divider.setStyleSheet(f"color: {BORDER}; background-color: {BORDER}; max-width: 1px;")
        content_layout.addWidget(vertical_divider)
        content_layout.addWidget(self.info_panel)

    def set_repository(self, repository):
        self.graph_panel.set_repository(repository)
        first_commit = repository.get_commit(repository.selected_commit_hash)
        if first_commit:
            self.info_panel.set_commit(first_commit)
