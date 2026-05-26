from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QWidget,
    QInputDialog,
)

from ableton_vcs.config.theme import *
from ableton_vcs.data.commit_repository import CommitRepository
from ableton_vcs.ui.screens.main_surface import MainSurface
from ableton_vcs.ui.dialogs.commit_form_dialog import CommitFormDialog
from ableton_vcs.ui.common.app_title import AppTitle
from ableton_vcs.services.project_service import ProjectService


class LandingPage(QWidget):
    def __init__(self):
        super().__init__()

        self.repository = CommitRepository()
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
        self.surface.header.open_button.clicked.connect(self.open_selected_commit)
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
            self.open_project_folder(folder)

    def open_project_folder(self, folder):
        if not folder:
            return

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
            self.surface.load_uninitialized_project(folder)

            QMessageBox.information(
                self,
                "Git repository found",
                "This folder already has Git, but it is not initialized for WaveTrace yet."
            )

        elif project_state == "uninitialized":
            self.surface.load_uninitialized_project(folder)

        elif project_state == "not_ableton_project":
            self.surface.load_empty_project(folder)

            QMessageBox.information(
                self,
                "Not an Ableton project",
                "This folder does not contain an .als file."
            )

        else:
            self.surface.load_empty_project("")

    def open_selected_commit(self):
        if self.surface.current_project_state != "versioned":
            QMessageBox.information(
                self,
                "Open",
                "Please open or initialize a WaveTrace project first."
            )
            return

        selected_hash = self.surface.default_content.graph_panel.graph.selected_hash

        if not selected_hash:
            selected_hash = self.surface.repository.selected_commit_hash

        if not selected_hash:
            QMessageBox.information(
                self,
                "Open",
                "Please select a commit first."
            )
            return

        try:
            als_path = self.project_service.open_commit_version(
                project_path=self.surface.current_folder,
                commit_hash=selected_hash
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Open failed",
                str(error)
            )
            return

        metadata = self.project_service.load_project_metadata(self.surface.current_folder)

        if metadata is not None:
            self.surface.load_versioned_project(self.surface.current_folder, metadata)

        QMessageBox.information(
            self,
            "Version opened",
            f"Opened Ableton file:\n{als_path}"
        )

    def merge_action(self):
        self.surface.enter_merge_mode()

    def commit_pending_changes(self):
        if self.surface.current_project_state != "versioned":
            QMessageBox.information(
                self,
                "Commit",
                "Please open or initialize a WaveTrace project first."
            )
            return

        if not self.surface.current_folder:
            QMessageBox.warning(
                self,
                "Commit",
                "No project folder is selected."
            )
            return

        dialog = CommitFormDialog("New commit", self)
        dialog.name_input.setPlaceholderText("e.g. vocal level fixes")
        dialog.comment_input.setPlaceholderText("Describe what changed in this version...")

        if dialog.exec() != QDialog.Accepted:
            return

        commit_name = dialog.name_input.text().strip() or "New commit"
        commit_comment = dialog.comment_input.toPlainText().strip() or "Committed latest changes."
        wav_path = dialog.selected_wav_path or ""

        metadata_before_commit = self.project_service.load_project_metadata(
            self.surface.current_folder
        )

        branch_name = None

        if metadata_before_commit and metadata_before_commit.get("working_mode") == "detached_experiment":
            branch_name, ok = QInputDialog.getText(
                self,
                "Save as branch",
                "You are committing changes from an older version.\nEnter a branch name:"
            )

            if not ok:
                return

            branch_name = branch_name.strip()

            if not branch_name:
                QMessageBox.warning(
                    self,
                    "Branch name required",
                    "Please enter a branch name to save this version."
                )
                return

        try:
            metadata = self.project_service.create_commit(
                project_path=self.surface.current_folder,
                name=commit_name,
                comment=commit_comment,
                audio_path=wav_path,
                branch_name=branch_name
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Commit failed",
                str(error)
            )
            return

        self.surface.load_versioned_project(
            self.surface.current_folder,
            metadata
        )

        QMessageBox.information(
            self,
            "Commit created",
            "New WaveTrace version was committed successfully."
        )

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
            QMessageBox.information(
                self,
                "Demo",
                "Demo merge committed. Returning to main page."
            )
            self.surface.exit_merge_mode()