from pathlib import Path
from PySide6.QtWidgets import QFileDialog, QMessageBox, QDialog, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from ableton_vcs.config.theme import *
from ableton_vcs.data.commit_repository import CommitRepository
from ableton_vcs.ui.common.pill_button import PillButton
from ableton_vcs.ui.screens.main_surface import MainSurface
from ableton_vcs.ui.dialogs.commit_form_dialog import CommitFormDialog
from ableton_vcs.ui.common.app_title import AppTitle
from ableton_vcs.services.project_service import ProjectService


class LandingPage(QWidget):
    def __init__(self):
        super().__init__()
        self.repository = CommitRepository(Path(__file__).resolve().parents[2] / "dummy_commits.json")
        self.project_service = ProjectService()
        self.setAutoFillBackground(True)
        self.build_ui()

    def build_ui(self):
        self.setStyleSheet(
            f"""
            QWidget {{ background-color: {BG_MAIN}; font-family: Arial; }}
            QMainWindow {{ background-color: {BG_MAIN}; }}
            QMessageBox {{ background-color: {BG_MAIN}; }}
            """
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 22)
        root.setSpacing(16)
        root.addWidget(AppTitle())
        self.surface = MainSurface(self.repository, self.project_service)
        root.addWidget(self.surface, 1)
        self.surface.header.browse_button.clicked.connect(self.browse_folder)
        self.surface.header.open_button.clicked.connect(self.open_project)
        self.surface.header.merge_button.clicked.connect(self.merge_action)
        self.surface.header.commit_button.clicked.connect(self.commit_pending_changes)
        self.surface.header.close_button.clicked.connect(self.close_merge_mode)
        self.surface.header.select_button.clicked.connect(self.select_merge_commits)
        self.surface.header.merge_confirm_button.clicked.connect(self.commit_merge)
        self.surface.header.initialize_button.clicked.connect(self.surface.request_initialize)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Ableton Project Folder",
            str(Path.home())
        )

        if folder:
            self.surface.header.folder_input.set_path(folder)

            project_state = self.project_service.get_project_state(folder)

            if project_state == "versioned":
                metadata = self.project_service.load_project_metadata(folder)

                if metadata is None:
                    QMessageBox.warning(
                        self,
                        "WaveTrace",
                        "This project has a WaveTrace link, but its metadata file could not be found."
                    )
                    return

                self.surface.load_versioned_project(folder, metadata)

            elif project_state == "git_only":
                self.surface.current_folder = folder
                self.surface.current_project_state = "uninitialized"
                self.surface.header.set_mode("uninitialized")
                self.surface.show_screen("uninitialized")

                QMessageBox.information(
                    self,
                    "Git repository found",
                    "This folder already has Git, but it is not initialized for WaveTrace yet."
                )

            elif project_state == "uninitialized":
                self.surface.current_folder = folder
                self.surface.current_project_state = "uninitialized"
                self.surface.header.set_mode("uninitialized")
                self.surface.show_screen("uninitialized")

            elif project_state == "not_ableton_project":
                self.surface.current_folder = folder
                self.surface.current_project_state = "empty"
                self.surface.header.set_mode("default")
                self.surface.show_screen("empty")

            else:
                self.surface.current_folder = ""
                self.surface.current_project_state = "empty"
                self.surface.header.set_mode("default")
                self.surface.show_screen("empty")

    def open_project(self):
        self.surface.set_project_from_path(self.surface.header.folder_input.label.text())

    def merge_action(self):
        self.surface.enter_merge_mode()

    def commit_pending_changes(self):
        repo = self.surface.active_repository()
        graph = self.surface.default_content.graph_panel.graph
        selected_commit = repo.get_commit(graph.selected_hash)
        if not selected_commit or not selected_commit.get("is_pending"):
            return

        dialog = CommitFormDialog("New commit", self)
        dialog.name_input.setPlaceholderText("e.g. vocal level fixes")
        dialog.comment_input.setPlaceholderText("Describe what changed in this version...")
        if dialog.exec() != QDialog.Accepted:
            return

        old_hash = selected_commit["hash"]
        new_hash = f"c{len([commit for commit in repo.commits if not commit.get('is_pending')]) + 1}"

        for commit in repo.commits:
            commit["successors"] = [new_hash if successor_hash == old_hash else successor_hash for successor_hash in commit["successors"]]
            commit["predecessors"] = [new_hash if predecessor_hash == old_hash else predecessor_hash for predecessor_hash in commit["predecessors"]]

        selected_commit["hash"] = new_hash
        selected_commit["name"] = dialog.name_input.text().strip() or "New commit"
        selected_commit["comment"] = dialog.comment_input.toPlainText().strip() or "Committed latest changes."
        selected_commit["date"] = "2026-04-21 12:00"
        selected_commit["audio_path"] = dialog.selected_wav_path or selected_commit["audio_path"]
        selected_commit["is_pending"] = False
        repo.data["selected_commit"] = new_hash
        repo.refresh_from_data()
        self.surface.default_content.set_repository(repo)
        self.surface.header.set_mode(self.surface.current_project_state)
        self.surface.header.set_commit_enabled(False)
        self.surface.handle_commit_selected(new_hash)

    def close_merge_mode(self):
        self.surface.exit_merge_mode()

    def select_merge_commits(self):
        if len(self.surface.default_content.graph_panel.graph.merge_selected_hashes) == 2:
            self.surface.show_merge_layout()

    def commit_merge(self):
        if self.surface.merge_layout_widget is None or not self.surface.merge_layout_widget.isVisible():
            return
        dialog = CommitFormDialog("New merge commit", self)
        dialog.name_input.setPlaceholderText("e.g. merged vocal branch")
        dialog.comment_input.setPlaceholderText("Describe what this merge includes...")
        result = dialog.exec()
        if result == QDialog.Accepted:
            QMessageBox.information(self, "Demo", "Demo merge committed. Returning to main page.")
            self.surface.exit_merge_mode()
