from PySide6.QtWidgets import QHBoxLayout, QWidget
from ableton_vcs.ui.common.pill_button import PillButton
from ableton_vcs.ui.common.folder_input import FolderInput

class HeaderBar(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        self.browse_button = PillButton("Browse")
        self.folder_input = FolderInput()
        self.initialize_button = PillButton("Initialize", primary=True)
        self.merge_button = PillButton("Merge", primary=True)
        self.commit_button = PillButton("Commit", primary=True)
        self.open_button = PillButton("Open")
        self.select_button = PillButton("Select", primary=True, compact=True)
        self.merge_confirm_button = PillButton("Merge", primary=True, compact=True)
        self.close_button = PillButton("Close", compact=True)
        layout.addWidget(self.browse_button)
        layout.addWidget(self.folder_input, 1)
        layout.addWidget(self.initialize_button)
        layout.addWidget(self.merge_button)
        layout.addWidget(self.commit_button)
        layout.addWidget(self.open_button)
        layout.addWidget(self.select_button)
        layout.addWidget(self.merge_confirm_button)
        layout.addWidget(self.close_button)
        self.initialize_button.hide()
        self.select_button.hide()
        self.merge_confirm_button.hide()
        self.close_button.hide()
        self.select_button.set_primary_enabled(False)
        self.commit_button.set_primary_enabled(False)

    def set_mode(self, mode):
        self.browse_button.show()
        self.folder_input.show()
        self.open_button.show()

        self.initialize_button.setVisible(mode == "uninitialized")
        self.merge_button.setVisible(mode in ["versioned", "initialized"])
        self.commit_button.setVisible(mode in ["versioned", "initialized"])
        self.select_button.setVisible(mode == "select")
        self.merge_confirm_button.setVisible(mode == "merge_layout")
        self.close_button.setVisible(mode in ["select", "merge_layout"])

    def set_select_enabled(self, enabled):
        self.select_button.set_primary_enabled(enabled)

    def set_commit_enabled(self, enabled):
        self.commit_button.set_primary_enabled(enabled)
