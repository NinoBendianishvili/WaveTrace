from PySide6.QtWidgets import QHBoxLayout, QWidget
from ableton_vcs.data.dummy_data import build_demo_merge_groups
from ableton_vcs.ui.merge.merge_side_panel import MergeSidePanel

class MergePlaceholder(QWidget):
    def __init__(self, left_commit_name, right_commit_name):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)
        groups = build_demo_merge_groups()
        self.left_panel = MergeSidePanel("Left", left_commit_name, groups)
        self.right_panel = MergeSidePanel("Right", right_commit_name, groups)
        layout.addWidget(self.left_panel, 1)
        layout.addWidget(self.right_panel, 1)
