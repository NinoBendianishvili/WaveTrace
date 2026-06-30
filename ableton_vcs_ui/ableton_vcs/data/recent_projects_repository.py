import json
from datetime import datetime
from pathlib import Path

from ableton_vcs.config.app_paths import (
    DEFAULT_RECENT_PROJECTS_DATA,
    RECENT_PROJECTS_FILE,
    ensure_app_data_files,
)


class RecentProjectsRepository:
    """Stores local recent-project shortcuts.

    This file is intentionally machine-specific. It stores current paths for UI
    convenience, while the real project metadata lives inside each Ableton
    project folder at .wavetrace/project.json.
    """

    MAX_RECENT_PROJECTS = 10

    def __init__(self):
        ensure_app_data_files()

    def default_data(self):
        return {
            "schema_version": DEFAULT_RECENT_PROJECTS_DATA["schema_version"],
            "last_opened_project": "",
            "last_opened_project_id": "",
            "projects": [],
        }

    def load_raw(self):
        ensure_app_data_files()

        try:
            with RECENT_PROJECTS_FILE.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            return self.default_data()

    def load(self):
        data = self.normalize_data(self.load_raw())
        self.save(data)
        return data

    def save(self, data):
        ensure_app_data_files()

        with RECENT_PROJECTS_FILE.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def normalize_data(self, data):
        normalized = self.default_data()

        if not isinstance(data, dict):
            return normalized

        raw_projects = data.get("projects")

        # Backward compatibility with the old format:
        # {"last_opened_project": "...", "recent_projects": ["path1", "path2"]}
        if raw_projects is None:
            raw_projects = data.get("recent_projects", [])

        projects = []

        if isinstance(raw_projects, list):
            for item in raw_projects:
                entry = self.normalize_entry(item)

                if entry:
                    projects.append(entry)

        normalized["projects"] = self.deduplicate_projects(projects)[:self.MAX_RECENT_PROJECTS]

        last_opened_project = data.get("last_opened_project", "")
        last_opened_project_id = data.get("last_opened_project_id", "")

        if normalized["projects"]:
            first = normalized["projects"][0]
            normalized["last_opened_project"] = first.get("path", last_opened_project)
            normalized["last_opened_project_id"] = first.get("project_id", last_opened_project_id)
        else:
            normalized["last_opened_project"] = last_opened_project
            normalized["last_opened_project_id"] = last_opened_project_id

        return normalized

    def normalize_entry(self, item):
        if isinstance(item, dict):
            raw_path = item.get("path", "")
            metadata = item
        else:
            raw_path = str(item or "")
            metadata = {}

        if not raw_path:
            return None

        path = Path(raw_path).expanduser()

        try:
            resolved_path = str(path.resolve())
        except OSError:
            resolved_path = str(path)

        folder_metadata = self.read_project_metadata(resolved_path)

        project_id = (
            metadata.get("project_id")
            or folder_metadata.get("project_id", "")
        )
        project_name = (
            metadata.get("project_name")
            or folder_metadata.get("project_name", "")
            or Path(resolved_path).name
        )
        ableton_set_file = (
            metadata.get("ableton_set_file")
            or folder_metadata.get("ableton_set_file", "")
            or self.find_ableton_set_file(resolved_path)
        )
        last_opened_at = metadata.get("last_opened_at") or datetime.now().strftime("%Y-%m-%d %H:%M")

        return {
            "project_id": project_id,
            "project_name": project_name,
            "path": resolved_path,
            "last_opened_at": last_opened_at,
            "ableton_set_file": ableton_set_file,
        }

    def make_project_entry(self, project_path, metadata=None):
        project_path = Path(project_path).expanduser().resolve()
        metadata = metadata or self.read_project_metadata(project_path)

        return {
            "project_id": metadata.get("project_id", ""),
            "project_name": metadata.get("project_name") or project_path.name,
            "path": str(project_path),
            "last_opened_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ableton_set_file": metadata.get("ableton_set_file") or self.find_ableton_set_file(project_path),
        }

    def read_project_metadata(self, project_path):
        project_path = Path(project_path).expanduser()
        metadata_path = project_path / ".wavetrace" / "project.json"

        if not metadata_path.exists():
            return {}

        try:
            with metadata_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, OSError):
            return {}

        return data if isinstance(data, dict) else {}

    def find_ableton_set_file(self, project_path):
        project_path = Path(project_path).expanduser()

        if not project_path.exists() or not project_path.is_dir():
            return ""

        als_files = sorted(project_path.glob("*.als"))

        if not als_files:
            return ""

        return als_files[0].name

    def deduplicate_projects(self, projects):
        deduped = []
        seen_project_ids = set()
        seen_paths = set()

        for entry in projects:
            project_id = entry.get("project_id", "")
            path = entry.get("path", "")

            if project_id:
                if project_id in seen_project_ids:
                    continue

                seen_project_ids.add(project_id)
            else:
                if path in seen_paths:
                    continue

            seen_paths.add(path)
            deduped.append(entry)

        return deduped

    def save_project(self, project_path, metadata=None):
        entry = self.make_project_entry(project_path, metadata)

        data = self.load()
        projects = data.get("projects", [])

        project_id = entry.get("project_id", "")
        path = entry.get("path", "")

        filtered_projects = []

        for existing in projects:
            existing_project_id = existing.get("project_id", "")
            existing_path = existing.get("path", "")

            same_project = bool(project_id and existing_project_id == project_id)
            same_path = existing_path == path

            if same_project or same_path:
                continue

            filtered_projects.append(existing)

        filtered_projects.insert(0, entry)
        filtered_projects = self.deduplicate_projects(filtered_projects)[:self.MAX_RECENT_PROJECTS]

        data["last_opened_project"] = entry["path"]
        data["last_opened_project_id"] = entry.get("project_id", "")
        data["projects"] = filtered_projects

        self.save(data)

    def get_last_opened_project(self):
        data = self.load()
        return data.get("last_opened_project", "")

    def get_recent_projects(self):
        data = self.load()
        return data.get("projects", [])