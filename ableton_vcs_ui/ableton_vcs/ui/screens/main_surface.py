from PySide6.QtWidgets import QDialog, QFrame, QMessageBox, QVBoxLayout, QWidget

from ableton_vcs.config.theme import *
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
        self.project_service = project_service

        self.current_project_state = "empty"
        self.current_folder = ""
        self.merge_layout_widget = None

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
        divider.setStyleSheet(
            f"color: {BORDER}; background-color: {BORDER}; max-height: 1px;"
        )

        self.content_host = QVBoxLayout()
        self.content_host.setContentsMargins(0, 0, 0, 0)
        self.content_host.setSpacing(0)

        content_wrap = QWidget()
        content_wrap.setLayout(self.content_host)

        layout.addWidget(header_wrap)
        layout.addWidget(divider)
        layout.addWidget(content_wrap, 1)

        self.empty_widget = EmptyStateWidget("select a project from browse")

        self.uninitialized_widget = EmptyStateWidget(
            "this project is not initialized for versioning yet",
            with_button=True,
            button_text="Initialize"
        )

        self.default_content = DefaultContent(repository)

        self.content_host.addWidget(self.empty_widget)
        self.content_host.addWidget(self.uninitialized_widget)
        self.content_host.addWidget(self.default_content)

        self.default_content.graph_panel.graph.commit_selected.connect(
            self.handle_commit_selected
        )
        self.default_content.graph_panel.graph.merge_selection_changed.connect(
            self.handle_merge_selection_changed
        )

        self.uninitialized_widget.button.clicked.connect(self.request_initialize)

        self.load_empty_project("")

    def show_screen(self, screen):
        self.empty_widget.setVisible(screen == "empty")
        self.uninitialized_widget.setVisible(screen == "uninitialized")
        self.default_content.setVisible(screen == "default")

        if self.merge_layout_widget is not None:
            self.merge_layout_widget.setVisible(screen == "merge")

    def active_repository(self):
        return self.repository

    def load_versioned_project(self, folder, metadata):
        self.exit_merge_mode(silent=True)

        self.current_folder = str(folder)
        self.current_project_state = "versioned"

        self.repository = CommitRepository(data=metadata)

        self.default_content.set_repository(self.repository)
        self.header.set_mode("versioned")
        self.header.set_commit_enabled(True)
        self.show_screen("default")

        selected_commit_hash = self.repository.selected_commit_hash

        if selected_commit_hash:
            self.handle_commit_selected(selected_commit_hash)

    def load_uninitialized_project(self, folder):
        self.exit_merge_mode(silent=True)

        self.current_folder = str(folder)
        self.current_project_state = "uninitialized"

        self.header.set_mode("uninitialized")
        self.header.set_commit_enabled(False)
        self.show_screen("uninitialized")

    def load_empty_project(self, folder):
        self.exit_merge_mode(silent=True)

        self.current_folder = str(folder) if folder else ""
        self.current_project_state = "empty"

        self.header.set_mode("default")
        self.header.set_commit_enabled(False)
        self.show_screen("empty")

    def request_initialize(self):
        if not self.current_folder:
            QMessageBox.warning(
                self,
                "Initialize",
                "Please select a project folder first."
            )
            return

        dialog = CommitFormDialog("Initialize project", self)
        dialog.name_input.setPlaceholderText("e.g. initial project")
        dialog.comment_input.setPlaceholderText(
            "Describe the starting state of the project..."
        )

        result = dialog.exec()

        if result != QDialog.Accepted:
            return

        commit_name = dialog.name_input.text().strip() or "Initial commit"
        commit_comment = (
            dialog.comment_input.toPlainText().strip()
            or "Project initialized for versioning."
        )
        wav_path = dialog.selected_wav_path or ""

        try:
            metadata = self.project_service.initialize_project(
                project_path=self.current_folder,
                first_commit_name=commit_name,
                first_commit_comment=commit_comment,
                audio_path=wav_path
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Initialize failed",
                str(error)
            )
            return

        self.load_versioned_project(self.current_folder, metadata)

        QMessageBox.information(
            self,
            "Project initialized",
            "WaveTrace versioning was initialized successfully."
        )

    def handle_commit_selected(self, commit_hash):
        commit = self.active_repository().get_commit(commit_hash)

        if not commit:
            return

        self.default_content.info_panel.set_commit(commit)

    def handle_merge_selection_changed(self, selected_hashes):
        self.header.set_select_enabled(len(selected_hashes) == 2)

        repo = self.active_repository()

        if len(selected_hashes) == 1:
            commit = repo.get_commit(selected_hashes[0])

            if commit:
                self.default_content.info_panel.set_commit(commit)

        elif len(selected_hashes) == 2:
            first_commit = repo.get_commit(selected_hashes[0])
            second_commit = repo.get_commit(selected_hashes[1])

            if first_commit and second_commit:
                self.default_content.info_panel.set_merge_preview(
                    first_commit,
                    second_commit
                )

        elif len(selected_hashes) == 0:
            selected_hash = self.default_content.graph_panel.graph.selected_hash

            if selected_hash:
                self.handle_commit_selected(selected_hash)

    def enter_merge_mode(self):
        if self.current_project_state != "versioned":
            return

        if len(self.active_repository().commits) < 2:
            QMessageBox.information(
                self,
                "Merge",
                "At least two commits are needed to open merge mode."
            )
            return

        self.header.set_mode("select")
        self.header.set_select_enabled(False)
        self.header.set_commit_enabled(False)

        self.default_content.graph_panel.graph.set_merge_mode(True)
        self.show_screen("default")

    def exit_merge_mode(self, silent=False):
        graph = self.default_content.graph_panel.graph
        graph.set_merge_mode(False)

        if self.merge_layout_widget is not None:
            self.merge_layout_widget.hide()

        if silent:
            return

        if self.current_project_state == "versioned":
            self.header.set_mode("versioned")
            self.header.set_commit_enabled(True)
            self.show_screen("default")

            if graph.selected_hash:
                self.handle_commit_selected(graph.selected_hash)

        elif self.current_project_state == "uninitialized":
            self.header.set_mode("uninitialized")
            self.header.set_commit_enabled(False)
            self.show_screen("uninitialized")

        else:
            self.header.set_mode("default")
            self.header.set_commit_enabled(False)
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

        comparison_rows = self.project_service.compare_commits_for_merge(
            first_commit,
            second_commit
        )

        if self.merge_layout_widget is not None:
            self.content_host.removeWidget(self.merge_layout_widget)
            self.merge_layout_widget.deleteLater()

        self.merge_layout_widget = MergePlaceholder(
            first_commit,
            second_commit,
            comparison_rows
        )

        self.content_host.addWidget(self.merge_layout_widget)

        self.header.set_mode("merge_layout")
        self.header.set_commit_enabled(False)
        self.show_screen("merge")