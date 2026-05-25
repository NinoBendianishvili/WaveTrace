import json
from pathlib import Path
from datetime import datetime

from ableton_vcs.data.recent_projects_repository import RecentProjectsRepository
from ableton_vcs.data.project_metadata_repository import ProjectMetadataRepository
from ableton_vcs.services.git_service import GitService


class ProjectService:
    def __init__(self):
        self.recent_projects_repository = RecentProjectsRepository()
        self.project_metadata_repository = ProjectMetadataRepository()
        self.git_service = GitService()

    def remember_project(self, project_path):
        self.recent_projects_repository.save_project(project_path)

    def get_last_opened_project(self):
        return self.recent_projects_repository.get_last_opened_project()

    def get_recent_projects(self):
        return self.recent_projects_repository.get_recent_projects()

    def is_ableton_project(self, project_path):
        project_path = Path(project_path)

        if not project_path.exists() or not project_path.is_dir():
            return False

        return len(list(project_path.glob("*.als"))) > 0

    def has_git_repository(self, project_path):
        project_path = Path(project_path)
        return (project_path / ".git").exists()

    def is_wavetrace_initialized(self, project_path):
        project_path = Path(project_path)
        return (project_path / ".wavetrace" / "project.json").exists()

    def get_project_state(self, project_path):
        project_path = Path(project_path)

        self.remember_project(project_path)

        if not project_path.exists() or not project_path.is_dir():
            return "invalid"

        if not self.is_ableton_project(project_path):
            return "not_ableton_project"

        has_git = self.has_git_repository(project_path)
        has_wavetrace = self.is_wavetrace_initialized(project_path)

        if has_git and has_wavetrace:
            return "versioned"

        if has_git and not has_wavetrace:
            return "git_only"

        return "uninitialized"

    def initialize_project(self, project_path, first_commit_name, first_commit_comment, audio_path):
        project_path = Path(project_path).resolve()

        wavetrace_dir = project_path / ".wavetrace"
        wavetrace_dir.mkdir(parents=True, exist_ok=True)

        self.git_service.init_repository(project_path)

        project_id = self.project_metadata_repository.make_project_id()

        link_data = {
            "project_id": project_id,
            "project_name": project_path.name,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

        link_file = wavetrace_dir / "project.json"

        with link_file.open("w", encoding="utf-8") as file:
            json.dump(link_data, file, indent=4)

        git_commit_hash = self.git_service.create_initial_commit(
            project_path,
            first_commit_name
        )

        metadata = self.project_metadata_repository.create_project_metadata(
            project_path=project_path,
            first_commit_name=first_commit_name,
            first_commit_comment=first_commit_comment,
            audio_path=audio_path,
            git_commit_hash=git_commit_hash,
            project_id=project_id
        )

        self.remember_project(project_path)

        return metadata

    def load_project_metadata(self, project_path):
        return self.project_metadata_repository.load_from_project_folder(project_path)