from pathlib import Path

from PySide6.QtCore import QTimer
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
from ableton_vcs.ui.dialogs.plugin_list_dialog import PluginListDialog

class LandingPage(QWidget):
    def __init__(self):
        super().__init__()

        self.repository = CommitRepository()
        self.project_service = ProjectService()

        self.setAutoFillBackground(True)

        self.build_ui()
        self.refresh_recent_projects()

        self.pending_changes_timer = QTimer(self)
        self.pending_changes_timer.setInterval(10000)
        self.pending_changes_timer.timeout.connect(self.refresh_pending_changes)
        self.pending_changes_timer.start()

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

        self.surface.header.browse_folder_requested.connect(self.browse_folder)
        self.surface.header.recent_project_selected.connect(self.open_recent_project)

        self.surface.header.open_button.clicked.connect(self.open_selected_commit)
        self.surface.header.merge_button.clicked.connect(self.merge_action)
        self.surface.header.commit_button.clicked.connect(self.commit_pending_changes)
        self.surface.header.close_button.clicked.connect(self.close_merge_mode)
        self.surface.header.select_button.clicked.connect(self.select_merge_commits)
        self.surface.header.merge_confirm_button.clicked.connect(self.commit_merge)
        self.surface.header.initialize_button.clicked.connect(self.surface.request_initialize)

        self.surface.default_content.graph_panel.graph.pending_node_action_requested.connect(
            self.handle_pending_node_action
        )
        self.surface.default_content.info_panel.list_plugins_requested.connect(self.show_plugin_list)

    def refresh_recent_projects(self):
        recent_projects = self.project_service.get_recent_projects()
        self.surface.header.set_recent_projects(recent_projects)

    def refresh_pending_changes(self):
        if self.surface.current_project_state != "versioned":
            self.surface.default_content.graph_panel.set_pending_changes(False)
            return

        if not self.surface.current_folder:
            self.surface.default_content.graph_panel.set_pending_changes(False)
            return

        try:
            has_pending_changes = self.project_service.has_uncommitted_changes(
                self.surface.current_folder
            )
        except Exception:
            has_pending_changes = False

        self.surface.default_content.graph_panel.set_pending_changes(
            has_pending_changes
        )

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Ableton Project Folder",
            str(Path.home())
        )

        if folder:
            self.open_project_folder(folder)

    def open_recent_project(self, folder):
        if not folder:
            return

        path = Path(folder).expanduser()

        if not path.exists() or not path.is_dir():
            self.refresh_recent_projects()
            return

        self.open_project_folder(str(path))

    def open_project_folder(self, folder):
        if not folder:
            return

        self.surface.header.folder_input.set_path(folder)

        project_state = self.project_service.get_project_state(folder)

        self.refresh_recent_projects()

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
            self.refresh_pending_changes()

        elif project_state == "git_only":
            self.surface.load_uninitialized_project(folder)
            self.refresh_pending_changes()

            QMessageBox.information(
                self,
                "Git repository found",
                "This folder already has Git, but it is not initialized for WaveTrace yet."
            )

        elif project_state == "uninitialized":
            self.surface.load_uninitialized_project(folder)
            self.refresh_pending_changes()

        elif project_state == "not_ableton_project":
            self.surface.load_empty_project(folder)
            self.refresh_pending_changes()

            QMessageBox.information(
                self,
                "Not an Ableton project",
                "This folder does not contain an .als file."
            )

        else:
            self.surface.load_empty_project("")
            self.refresh_pending_changes()

    def handle_pending_node_action(self):
        message_box = QMessageBox(self)
        message_box.setWindowTitle("Uncommitted changes")
        message_box.setText("This project has changes that are not committed yet.")
        message_box.setInformativeText("What do you want to do with these changes?")

        commit_button = message_box.addButton("Commit", QMessageBox.AcceptRole)
        discard_button = message_box.addButton(
            "Discard changes",
            QMessageBox.DestructiveRole
        )
        ignore_button = message_box.addButton("Ignore", QMessageBox.RejectRole)

        message_box.exec()

        clicked_button = message_box.clickedButton()

        if clicked_button == commit_button:
            self.commit_pending_changes()
            return

        if clicked_button == discard_button:
            self.discard_pending_changes()
            return

        if clicked_button == ignore_button:
            return

    def handle_uncommitted_changes_before_switch(self):
        try:
            has_changes = self.project_service.has_uncommitted_changes(
                self.surface.current_folder
            )
        except Exception:
            has_changes = False

        if not has_changes:
            return True

        message_box = QMessageBox(self)
        message_box.setWindowTitle("Uncommitted changes")
        message_box.setText("You have uncommitted changes.")
        message_box.setInformativeText(
            "Before opening another version, choose what to do with the current changes."
        )

        commit_button = message_box.addButton("Commit", QMessageBox.AcceptRole)
        discard_button = message_box.addButton(
            "Discard changes",
            QMessageBox.DestructiveRole
        )
        cancel_button = message_box.addButton("Cancel", QMessageBox.RejectRole)

        message_box.exec()

        clicked_button = message_box.clickedButton()

        if clicked_button == commit_button:
            return self.commit_pending_changes()

        if clicked_button == discard_button:
            return self.discard_pending_changes()

        if clicked_button == cancel_button:
            return False

        return False

    def discard_pending_changes(self):
        confirm = QMessageBox.question(
            self,
            "Discard changes",
            "This will restore the project files on disk to the version they are currently based on.\n\n"
            "If this set is open in Ableton, WaveTrace will reopen the restored .als file after reset.\n\n"
            "Are you sure?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if confirm != QMessageBox.Yes:
            return False

        try:
            self.project_service.discard_uncommitted_changes(
                self.surface.current_folder
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Discard failed",
                str(error)
            )
            return False

        metadata = self.project_service.load_project_metadata(
            self.surface.current_folder
        )

        if metadata is not None:
            self.surface.load_versioned_project(
                self.surface.current_folder,
                metadata
            )

        self.surface.default_content.graph_panel.set_pending_changes(False)

        try:
            als_path = self.project_service.reopen_current_working_als(
                self.surface.current_folder
            )
        except Exception as error:
            QMessageBox.warning(
                self,
                "Reopen failed",
                f"Changes were discarded, but WaveTrace could not reopen the Ableton file:\n{error}"
            )
            return True

        QMessageBox.information(
            self,
            "Changes discarded",
            f"Project was reset to the version it was based on.\n\n"
            f"Reopened Ableton file:\n{als_path}"
        )

        return True
    def open_selected_commit(self):
        if self.surface.current_project_state != "versioned":
            QMessageBox.information(
                self,
                "Open",
                "Please open or initialize a WaveTrace project first."
            )
            return

        selected_hash = self.surface.default_content.graph_panel.graph.selected_hash

        if selected_hash == "__pending__":
            self.handle_pending_node_action()
            return

        if not selected_hash:
            selected_hash = self.surface.repository.selected_commit_hash

        if not selected_hash:
            QMessageBox.information(
                self,
                "Open",
                "Please select a commit first."
            )
            return

        if not self.handle_uncommitted_changes_before_switch():
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

        metadata = self.project_service.load_project_metadata(
            self.surface.current_folder
        )

        if metadata is not None:
            self.surface.load_versioned_project(
                self.surface.current_folder,
                metadata
            )

        self.refresh_pending_changes()

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
            return False

        if not self.surface.current_folder:
            QMessageBox.warning(
                self,
                "Commit",
                "No project folder is selected."
            )
            return False

        dialog = CommitFormDialog("New commit", self)
        dialog.name_input.setPlaceholderText("e.g. vocal level fixes")
        dialog.comment_input.setPlaceholderText("Describe what changed in this version...")

        if dialog.exec() != QDialog.Accepted:
            return False

        commit_name = dialog.name_input.text().strip() or "New commit"
        commit_comment = (
            dialog.comment_input.toPlainText().strip()
            or "Committed latest changes."
        )
        wav_path = dialog.selected_wav_path or ""

        metadata_before_commit = self.project_service.load_project_metadata(
            self.surface.current_folder
        )

        branch_name = None

        if (
            metadata_before_commit
            and metadata_before_commit.get("working_mode") == "detached_experiment"
        ):
            branch_name, ok = QInputDialog.getText(
                self,
                "Save as branch",
                "You are committing changes from an older version.\nEnter a branch name:"
            )

            if not ok:
                return False

            branch_name = branch_name.strip()

            if not branch_name:
                QMessageBox.warning(
                    self,
                    "Branch name required",
                    "Please enter a branch name to save this version."
                )
                return False

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
            return False

        self.surface.load_versioned_project(
            self.surface.current_folder,
            metadata
        )

        self.refresh_recent_projects()
        self.refresh_pending_changes()

        QMessageBox.information(
            self,
            "Commit created",
            "New WaveTrace version was committed successfully."
        )

        return True

    def close_merge_mode(self):
        self.surface.exit_merge_mode()

    def select_merge_commits(self):
        if len(self.surface.default_content.graph_panel.graph.merge_selected_hashes) == 2:
            self.surface.show_merge_layout()

    def commit_merge(self):
        if self.surface.merge_layout_widget is None or not self.surface.merge_layout_widget.isVisible():
            return

        selected_tracks = self.surface.merge_layout_widget.get_selected_tracks()

        left_commit = self.surface.merge_layout_widget.left_commit
        right_commit = self.surface.merge_layout_widget.right_commit

        dialog = CommitFormDialog("New merge commit", self)
        dialog.name_input.setPlaceholderText("e.g. merged vocal branch")
        dialog.comment_input.setPlaceholderText("Describe what this merge includes...")

        result = dialog.exec()

        if result != QDialog.Accepted:
            return

        commit_name = dialog.name_input.text().strip() or "Merge commit"
        commit_comment = (
            dialog.comment_input.toPlainText().strip()
            or f"Merged {left_commit.get('name', 'left')} and {right_commit.get('name', 'right')}."
        )
        wav_path = dialog.selected_wav_path or ""

        try:
            metadata = self.project_service.create_merge_commit(
                project_path=self.surface.current_folder,
                left_commit_hash=left_commit["hash"],
                right_commit_hash=right_commit["hash"],
                selected_left_global_ids=selected_tracks.get("left", []),
                selected_right_global_ids=selected_tracks.get("right", []),
                name=commit_name,
                comment=commit_comment,
                audio_path=wav_path,
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Merge failed",
                str(error)
            )
            return

        self.surface.exit_merge_mode(silent=True)
        self.surface.load_versioned_project(
            self.surface.current_folder,
            metadata,
        )

        self.refresh_recent_projects()

        if hasattr(self, "refresh_pending_changes"):
            self.refresh_pending_changes()

        QMessageBox.information(
            self,
            "Merge committed",
            "WaveTrace created a resolved Ableton merge commit successfully."
        )

    def show_plugin_list(self):
        if self.surface.current_project_state != "versioned":
            QMessageBox.information(
                self,
                "Plugins",
                "Please open or initialize a WaveTrace project first."
            )
            return

        selected_hash = self.surface.default_content.graph_panel.graph.selected_hash

        if selected_hash == "__pending__":
            selected_hash = None

        if not selected_hash:
            selected_hash = self.surface.repository.selected_commit_hash

        try:
            if selected_hash:
                plugins = self.project_service.list_plugins_for_commit(
                    project_path=self.surface.current_folder,
                    commit_hash=selected_hash,
                )
                commit = self.surface.repository.get_commit(selected_hash)
                commit_name = commit.get("name", selected_hash) if commit else selected_hash
            else:
                plugins = self.project_service.list_plugins_for_current_project(
                    self.surface.current_folder
                )
                commit_name = "Current working project"

        except Exception as error:
            QMessageBox.critical(
                self,
                "Plugin extraction failed",
                str(error)
            )
            return

        dialog = PluginListDialog(
            plugins=plugins,
            commit_name=commit_name,
            parent=self,
        )
        dialog.exec()