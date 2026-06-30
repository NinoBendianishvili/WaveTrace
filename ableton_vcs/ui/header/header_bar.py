from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QHBoxLayout, QMenu, QWidget

from ableton_vcs.config.theme import *
from ableton_vcs.ui.common.pill_button import PillButton
from ableton_vcs.ui.common.folder_input import FolderInput


class HeaderBar(QWidget):
    browse_folder_requested = Signal()
    recent_project_selected = Signal(str)

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self.browse_button = PillButton("Browse ▾")
        self.browse_menu = QMenu(self)
        self.browse_button.setMenu(self.browse_menu)

        self.browse_menu.setStyleSheet(
            f"""
            QMenu {{
                background-color: {BG_PANEL};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 12px;
                padding: 8px;
                font-size: 13px;
            }}

            QMenu::item {{
                padding: 8px 24px 8px 12px;
                border-radius: 8px;
                background-color: transparent;
            }}

            QMenu::item:selected {{
                background-color: {BG_ELEMENT_HOVER};
            }}

            QMenu::item:disabled {{
                color: #707070;
                background-color: transparent;
            }}

            QMenu::separator {{
                height: 1px;
                background-color: {BORDER};
                margin: 8px 4px;
            }}
            """
        )

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

        self.set_recent_projects([])

    def set_recent_projects(self, recent_projects):
        self.browse_menu.clear()

        browse_action = QAction("Browse new folder...", self)
        browse_action.triggered.connect(self.browse_folder_requested.emit)
        self.browse_menu.addAction(browse_action)

        self.browse_menu.addSeparator()

        if not recent_projects:
            empty_action = QAction("No recent projects yet", self)
            empty_action.setEnabled(False)
            self.browse_menu.addAction(empty_action)
            return

        for recent_project in recent_projects:
            entry = self.normalize_recent_project(recent_project)

            if entry is None:
                continue

            path = Path(entry["path"]).expanduser()
            exists = path.exists() and path.is_dir()

            label = self.make_recent_project_label(entry, path, exists)
            action = QAction(label, self)
            action.setEnabled(exists)

            if exists:
                action.triggered.connect(
                    lambda checked=False, selected_path=str(path): self.recent_project_selected.emit(selected_path)
                )
            else:
                action.setToolTip("This project folder was not found in this location anymore.")

            self.browse_menu.addAction(action)

    def normalize_recent_project(self, recent_project):
        if isinstance(recent_project, dict):
            project_path = str(recent_project.get("path", "")).strip()

            if not project_path:
                return None

            return {
                "path": project_path,
                "project_name": recent_project.get("project_name", ""),
                "ableton_set_file": recent_project.get("ableton_set_file", ""),
            }

        project_path = str(recent_project or "").strip()

        if not project_path:
            return None

        return {
            "path": project_path,
            "project_name": Path(project_path).name,
            "ableton_set_file": "",
        }

    def make_recent_project_label(self, entry, path, exists):
        project_name = entry.get("project_name") or path.name or str(path)
        ableton_set_file = entry.get("ableton_set_file", "")

        if ableton_set_file:
            project_name = f"{project_name} ({ableton_set_file})"

        if exists:
            return f"{project_name}    {path}"

        return f"{project_name}    missing"

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