from pathlib import Path
from PySide6.QtWidgets import QDialog, QFrame, QMessageBox, QVBoxLayout, QWidget
from ableton_vcs.config.theme import *
from ableton_vcs.config.paths import VERSIONED_PROJECT_PATH, UNINITIALIZED_PROJECT_PATH
from ableton_vcs.data.commit_repository import CommitRepository
from ableton_vcs.ui.common.glass_card import GlassCard
from ableton_vcs.ui.common.empty_state import EmptyStateWidget
from ableton_vcs.ui.header.header_bar import HeaderBar
from ableton_vcs.ui.screens.default_content import DefaultContent
from ableton_vcs.ui.dialogs.commit_form_dialog import CommitFormDialog
from ableton_vcs.ui.merge.merge_placeholder import MergePlaceholder

class MainSurface(GlassCard):
    def __init__(self, repository, project_service):
        super().__init__(radius=30, border_color=BORDER, bg_color=BG_MAIN)
        self.repository = repository
        self.current_project_state = "empty"
        self.current_folder = ""
        self.merge_layout_widget = None
        self.initialized_repository = None
        self.project_service = project_service
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.header = HeaderBar()
        header_wrap = QWidget()
        header_layout = QVBoxLayout(header_wrap)
        header_layout.setContentsMargins(26, 18, 26, 18)
        header_layout.addWidget(self.header)
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"color: {BORDER}; background-color: {BORDER}; max-height: 1px;")
        self.content_host = QVBoxLayout()
        self.content_host.setContentsMargins(0, 0, 0, 0)
        self.content_host.setSpacing(0)
        content_wrap = QWidget()
        content_wrap.setLayout(self.content_host)
        layout.addWidget(header_wrap)
        layout.addWidget(divider)
        layout.addWidget(content_wrap, 1)

        self.empty_widget = EmptyStateWidget("select a project from browse")
        self.uninitialized_widget = EmptyStateWidget("this project is not initialized for versioning yet", with_button=True, button_text="Initialize")
        self.default_content = DefaultContent(repository)

        self.content_host.addWidget(self.empty_widget)
        self.content_host.addWidget(self.uninitialized_widget)
        self.content_host.addWidget(self.default_content)

        self.default_content.graph_panel.graph.commit_selected.connect(self.handle_commit_selected)
        self.default_content.graph_panel.graph.merge_selection_changed.connect(self.handle_merge_selection_changed)
        self.default_content.graph_panel.graph.pending_node_selected.connect(self.header.set_commit_enabled)
        self.uninitialized_widget.button.clicked.connect(self.request_initialize)

        self.show_screen("empty")

    def normalize_path(self, path_text):
        if not path_text:
            return ""
        normalized = str(Path(path_text))
        if not normalized.endswith("/"):
            normalized += "/"
        return normalized

    def show_screen(self, screen):
        self.empty_widget.setVisible(screen == "empty")
        self.uninitialized_widget.setVisible(screen == "uninitialized")
        self.default_content.setVisible(screen == "default")
        if self.merge_layout_widget is not None:
            self.merge_layout_widget.setVisible(screen == "merge")

    def set_project_from_path(self, folder):
        self.current_folder = folder
        normalized = self.normalize_path(folder)
        versioned_path = self.normalize_path(VERSIONED_PROJECT_PATH)
        uninitialized_path = self.normalize_path(UNINITIALIZED_PROJECT_PATH)

        self.exit_merge_mode(silent=True)

        if normalized == versioned_path:
            self.ensure_pending_node_for_versioned_project()
            self.current_project_state = "versioned"
            self.default_content.set_repository(self.repository)
            self.header.set_mode("versioned")
            self.show_screen("default")
            self.handle_commit_selected(self.repository.selected_commit_hash)
            return

        if normalized == uninitialized_path:
            if self.initialized_repository is None:
                self.current_project_state = "uninitialized"
                self.header.set_mode("uninitialized")
                self.show_screen("uninitialized")
            else:
                self.current_project_state = "initialized"
                self.default_content.set_repository(self.initialized_repository)
                self.header.set_mode("initialized")
                self.show_screen("default")
                self.handle_commit_selected(self.initialized_repository.selected_commit_hash)
            return

        self.current_project_state = "empty"
        self.header.set_mode("default")
        self.show_screen("empty")

    
    def load_versioned_project(self, folder, metadata):
        self.current_folder = str(folder)
        self.current_project_state = "versioned"

        self.repository = CommitRepository(data=metadata)

        self.default_content.set_repository(self.repository)
        self.header.set_mode("versioned")
        self.show_screen("default")

        selected_commit_hash = self.repository.selected_commit_hash
        self.handle_commit_selected(selected_commit_hash)

    def ensure_pending_node_for_versioned_project(self):
        if self.repository.pending_commit() is not None:
            return
        head_commit = next((commit for commit in self.repository.commits if not commit["successors"] and not commit.get("is_pending")), None)
        if head_commit is None:
            return
        pending_hash = "pending_changes"
        head_commit["successors"].append(pending_hash)
        pending_commit = {
            "hash": pending_hash,
            "name": "Uncommitted changes",
            "date": "",
            "comment": "Changes were made after the latest commit.",
            "audio_path": head_commit["audio_path"],
            "predecessors": [head_commit["hash"]],
            "successors": [],
            "lane": head_commit["lane"],
            "y": max(head_commit["y"] - 120, 30),
            "is_pending": True,
        }
        self.repository.commits.append(pending_commit)
        self.repository.data["selected_commit"] = self.repository.selected_commit_hash
        self.repository.refresh_from_data()

    def request_initialize(self):
        if not self.current_folder:
            QMessageBox.warning(self, "Initialize", "Please select a project folder first.")
            return

        dialog = CommitFormDialog("Initialize project", self)
        dialog.name_input.setPlaceholderText("e.g. initial project")
        dialog.comment_input.setPlaceholderText("Describe the starting state of the project...")

        result = dialog.exec()

        if result != QDialog.Accepted:
            return

        commit_name = dialog.name_input.text().strip() or "Initial commit"
        commit_comment = dialog.comment_input.toPlainText().strip() or "Project initialized for versioning."
        wav_path = dialog.selected_wav_path or ""

        try:
            metadata = self.project_service.initialize_project(
                project_path=self.current_folder,
                first_commit_name=commit_name,
                first_commit_comment=commit_comment,
                audio_path=wav_path
            )
        except Exception as error:
            QMessageBox.critical(self, "Initialize failed", str(error))
            return

        self.initialized_repository = CommitRepository(data=metadata)

        self.current_project_state = "initialized"
        self.default_content.set_repository(self.initialized_repository)
        self.header.set_mode("initialized")
        self.show_screen("default")
        self.handle_commit_selected(self.initialized_repository.selected_commit_hash)
        
    def active_repository(self):
        if self.current_project_state == "initialized" and self.initialized_repository is not None:
            return self.initialized_repository
        return self.repository

    def handle_commit_selected(self, commit_hash):
        commit = self.active_repository().get_commit(commit_hash)
        if commit:
            if commit.get("is_pending"):
                self.default_content.info_panel.set_pending_commit(commit)
            else:
                self.default_content.info_panel.set_commit(commit)

    def handle_merge_selection_changed(self, selected_hashes):
        self.header.set_select_enabled(len(selected_hashes) == 2)
        repo = self.active_repository()
        if len(selected_hashes) == 1:
            commit = repo.get_commit(selected_hashes[0])
            if commit:
                self.default_content.info_panel.set_commit(commit)
        if len(selected_hashes) == 2:
            first_commit = repo.get_commit(selected_hashes[0])
            second_commit = repo.get_commit(selected_hashes[1])
            if first_commit and second_commit:
                self.default_content.info_panel.set_merge_preview(first_commit, second_commit)
        if len(selected_hashes) == 0 and self.default_content.graph_panel.graph.selected_hash:
            self.handle_commit_selected(self.default_content.graph_panel.graph.selected_hash)

    def enter_merge_mode(self):
        if self.current_project_state not in ["versioned", "initialized"]:
            return
        if len(self.active_repository().commits) < 2:
            QMessageBox.information(self, "Merge", "At least two commits are needed to open merge mode.")
            return
        self.header.set_mode("select")
        self.header.set_select_enabled(False)
        self.default_content.graph_panel.graph.set_merge_mode(True)
        self.show_screen("default")

    def exit_merge_mode(self, silent=False):
        graph = self.default_content.graph_panel.graph
        graph.set_merge_mode(False)
        self.header.set_commit_enabled(False)
        if self.merge_layout_widget is not None:
            self.merge_layout_widget.hide()
        if not silent:
            if self.current_project_state == "versioned":
                self.header.set_mode("versioned")
            elif self.current_project_state == "initialized":
                self.header.set_mode("initialized")
            elif self.current_project_state == "uninitialized":
                self.header.set_mode("uninitialized")
            else:
                self.header.set_mode("default")
        if self.current_project_state in ["versioned", "initialized"]:
            self.show_screen("default")
            if graph.selected_hash:
                self.handle_commit_selected(graph.selected_hash)
        elif self.current_project_state == "uninitialized":
            self.show_screen("uninitialized")
        else:
            self.show_screen("empty")

    def show_merge_layout(self):
        selected = self.default_content.graph_panel.graph.merge_selected_hashes
        if len(selected) != 2:
            return
        repo = self.active_repository()
        first_commit = repo.get_commit(selected[0])
        second_commit = repo.get_commit(selected[1])
        if not first_commit or not second_commit:
            return
        if self.merge_layout_widget is not None:
            self.content_host.removeWidget(self.merge_layout_widget)
            self.merge_layout_widget.deleteLater()
        self.merge_layout_widget = MergePlaceholder(first_commit["name"], second_commit["name"])
        self.content_host.addWidget(self.merge_layout_widget)
        self.header.set_mode("merge_layout")
        self.show_screen("merge")
