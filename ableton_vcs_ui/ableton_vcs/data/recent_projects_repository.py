import json
from pathlib import Path

from ableton_vcs.config.app_paths import (
    RECENT_PROJECTS_FILE,
    ensure_app_data_files,
)


class RecentProjectsRepository:
    def __init__(self):
        ensure_app_data_files()

    def load(self):
        ensure_app_data_files()

        with RECENT_PROJECTS_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)

    def save(self, data):
        ensure_app_data_files()

        with RECENT_PROJECTS_FILE.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def save_project(self, project_path):
        project_path = str(Path(project_path).resolve())

        data = self.load()
        recent_projects = data.get("recent_projects", [])

        if project_path in recent_projects:
            recent_projects.remove(project_path)

        recent_projects.insert(0, project_path)
        recent_projects = recent_projects[:10]

        data["last_opened_project"] = project_path
        data["recent_projects"] = recent_projects

        self.save(data)

    def get_last_opened_project(self):
        data = self.load()
        return data.get("last_opened_project", "")

    def get_recent_projects(self):
        data = self.load()
        return data.get("recent_projects", [])