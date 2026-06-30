import json
import uuid
from pathlib import Path
from datetime import datetime

from ableton_vcs.config.app_paths import (
    LEGACY_PROJECT_METADATA_DIR,
    PROJECT_METADATA_BACKUP_DIR,
    PROJECT_METADATA_BACKUP_INDEX_FILE,
    DEFAULT_BACKUP_INDEX_DATA,
    ensure_app_data_files,
)


class ProjectMetadataRepository:
    """Loads and saves WaveTrace project metadata.

    Main source of truth:
        <Ableton Project>/.wavetrace/project.json

    Backup mirror:
        ~/.wavetrace/backups/<project_id>/project.json

    The backup is only used for recovery when the project-local metadata is
    missing or corrupted. It never overrides a valid project-local file.
    """

    def __init__(self):
        ensure_app_data_files()

    def make_project_id(self):
        return uuid.uuid4().hex[:16]

    def get_metadata_path(self, project_path):
        project_path = Path(project_path).expanduser().resolve()
        return project_path / ".wavetrace" / "project.json"

    def get_legacy_metadata_path(self, project_id):
        return LEGACY_PROJECT_METADATA_DIR / f"{project_id}.json"

    def get_backup_project_dir(self, project_id):
        return PROJECT_METADATA_BACKUP_DIR / project_id

    def get_backup_metadata_path(self, project_id):
        return self.get_backup_project_dir(project_id) / "project.json"

    def get_ableton_set_file(self, project_path):
        project_path = Path(project_path).expanduser().resolve()
        als_files = sorted(project_path.glob("*.als"))

        if not als_files:
            return ""

        return als_files[0].name

    def now_string(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M")

    def create_empty_project_metadata(self, project_path, project_id):
        project_path = Path(project_path).expanduser().resolve()
        now = self.now_string()

        metadata = {
            "schema_version": 3,
            "project_id": project_id,
            "project_name": project_path.name,
            "ableton_set_file": self.get_ableton_set_file(project_path),
            "last_known_path": str(project_path),
            "created_at": now,
            "metadata_revision": 0,
            "metadata_updated_at": now,

            "selected_branch": "MAIN",
            "selected_commit": "",
            "branches": {
                "MAIN": ""
            },

            "working_base_commit": "",
            "working_mode": "normal",

            "global_track_id_counter": 0,
            "commits": []
        }

        self.save_metadata(metadata, project_path=project_path)
        return metadata

    def append_commit(self, metadata, commit_data):
        metadata["commits"].append(commit_data)
        metadata["selected_commit"] = commit_data["hash"]
        metadata["global_track_id_counter"] = commit_data["global_track_id_counter"]

        selected_branch = metadata["selected_branch"]
        metadata.setdefault("branches", {})
        metadata["branches"][selected_branch] = commit_data["hash"]

        self.save_metadata(metadata)
        return metadata

    def load_json_file(self, path):
        path = Path(path)

        if not path.exists():
            return None

        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, OSError):
            return None

        return data if isinstance(data, dict) else None

    def save_json_atomic(self, path, data):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        temp_path = path.with_name(f"{path.name}.tmp")

        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
            file.flush()

        temp_path.replace(path)

    def load_backup_index(self):
        ensure_app_data_files()

        data = self.load_json_file(PROJECT_METADATA_BACKUP_INDEX_FILE)

        if data is None:
            return {
                "schema_version": DEFAULT_BACKUP_INDEX_DATA["schema_version"],
                "projects": {}
            }

        data.setdefault("schema_version", 1)
        data.setdefault("projects", {})

        if not isinstance(data["projects"], dict):
            data["projects"] = {}

        return data

    def save_backup_index(self, index_data):
        self.save_json_atomic(PROJECT_METADATA_BACKUP_INDEX_FILE, index_data)

    def update_backup_index(self, metadata, project_path):
        project_id = metadata.get("project_id", "")

        if not project_id:
            return

        project_path = Path(project_path).expanduser().resolve()
        index_data = self.load_backup_index()

        index_data.setdefault("projects", {})
        index_data["projects"][project_id] = {
            "project_id": project_id,
            "project_name": metadata.get("project_name", project_path.name),
            "ableton_set_file": metadata.get("ableton_set_file", ""),
            "last_known_path": str(project_path),
            "last_backup_at": self.now_string(),
        }

        self.save_backup_index(index_data)

    def save_backup_copy(self, metadata, project_path):
        project_id = metadata.get("project_id", "")

        if not project_id:
            return

        backup_path = self.get_backup_metadata_path(project_id)
        self.save_json_atomic(backup_path, metadata)
        self.update_backup_index(metadata, project_path)

    def load_legacy_by_project_id(self, project_id):
        if not project_id:
            return None

        return self.load_json_file(self.get_legacy_metadata_path(project_id))

    def load_backup_by_project_id(self, project_id):
        if not project_id:
            return None

        return self.load_json_file(self.get_backup_metadata_path(project_id))

    def load_backup_by_project_path(self, project_path):
        project_path = Path(project_path).expanduser().resolve()
        project_path_string = str(project_path)

        index_data = self.load_backup_index()
        projects = index_data.get("projects", {})

        for project_id, entry in projects.items():
            if entry.get("last_known_path") == project_path_string:
                backup_metadata = self.load_backup_by_project_id(project_id)

                if backup_metadata is not None:
                    return backup_metadata

        # Fallback scan in case the index is missing or outdated.
        if not PROJECT_METADATA_BACKUP_DIR.exists():
            return None

        for backup_metadata_path in PROJECT_METADATA_BACKUP_DIR.glob("*/project.json"):
            backup_metadata = self.load_json_file(backup_metadata_path)

            if backup_metadata is None:
                continue

            if backup_metadata.get("last_known_path") == project_path_string:
                return backup_metadata

        return None

    def normalize_metadata(self, metadata, project_path):
        project_path = Path(project_path).expanduser().resolve()

        metadata.setdefault("schema_version", 3)

        try:
            metadata["schema_version"] = max(int(metadata.get("schema_version", 3)), 3)
        except (TypeError, ValueError):
            metadata["schema_version"] = 3

        metadata.setdefault("project_id", self.make_project_id())
        metadata.setdefault("project_name", project_path.name)
        metadata.setdefault("ableton_set_file", self.get_ableton_set_file(project_path))
        metadata.setdefault("created_at", self.now_string())

        metadata.setdefault("metadata_revision", 0)
        metadata.setdefault("metadata_updated_at", self.now_string())

        metadata.setdefault("selected_branch", "MAIN")
        metadata.setdefault("selected_commit", "")
        metadata.setdefault("branches", {"MAIN": ""})
        metadata.setdefault("working_base_commit", "")
        metadata.setdefault("working_mode", "normal")
        metadata.setdefault("global_track_id_counter", 0)
        metadata.setdefault("commits", [])

        # This path is local machine information and may change when the folder moves.
        metadata["last_known_path"] = str(project_path)

        # Remove old external metadata pointer from older project files.
        metadata.pop("metadata_path", None)

        return metadata

    def bump_metadata_revision(self, metadata):
        try:
            current_revision = int(metadata.get("metadata_revision", 0))
        except (TypeError, ValueError):
            current_revision = 0

        metadata["metadata_revision"] = current_revision + 1
        metadata["metadata_updated_at"] = self.now_string()

        return metadata

    def save_metadata(self, metadata, project_path=None):
        if not metadata.get("project_id"):
            raise ValueError("Cannot save metadata without project_id.")

        if project_path is None:
            project_path = metadata.get("last_known_path")

        if not project_path:
            raise ValueError("Cannot save metadata without a project path.")

        project_path = Path(project_path).expanduser().resolve()
        metadata = self.normalize_metadata(metadata, project_path)
        metadata = self.bump_metadata_revision(metadata)

        metadata_path = self.get_metadata_path(project_path)

        # Save the real portable project metadata first.
        self.save_json_atomic(metadata_path, metadata)

        # Save a recovery mirror in the user's home directory.
        self.save_backup_copy(metadata, project_path)

    def is_full_metadata(self, metadata):
        if not isinstance(metadata, dict):
            return False

        return "commits" in metadata or "branches" in metadata

    def restore_from_backup(self, project_path):
        project_path = Path(project_path).expanduser().resolve()

        backup_metadata = self.load_backup_by_project_path(project_path)

        if backup_metadata is None:
            return None

        backup_metadata = self.normalize_metadata(backup_metadata, project_path)
        self.save_metadata(backup_metadata, project_path=project_path)

        return backup_metadata

    def load_from_project_folder(self, project_path):
        project_path = Path(project_path).expanduser().resolve()
        metadata_path = self.get_metadata_path(project_path)

        metadata = self.load_json_file(metadata_path)

        # Case 1: project-local metadata is valid and complete.
        # This is the normal path and always has priority over the backup.
        if self.is_full_metadata(metadata):
            metadata = self.normalize_metadata(metadata, project_path)
            self.save_metadata(metadata, project_path=project_path)
            return metadata

        # Case 2: project-local file exists but is old lightweight format.
        # Try backup first, then old legacy storage.
        if isinstance(metadata, dict):
            project_id = metadata.get("project_id", "")

            backup_metadata = self.load_backup_by_project_id(project_id)

            if backup_metadata is not None:
                backup_metadata = self.normalize_metadata(backup_metadata, project_path)
                self.save_metadata(backup_metadata, project_path=project_path)
                return backup_metadata

            legacy_metadata = self.load_legacy_by_project_id(project_id)

            if legacy_metadata is not None:
                legacy_metadata = self.normalize_metadata(legacy_metadata, project_path)
                self.save_metadata(legacy_metadata, project_path=project_path)
                return legacy_metadata

            return None

        # Case 3: project-local file is missing or corrupted.
        # Recover from backup only if the backup index can match this folder path.
        restored_metadata = self.restore_from_backup(project_path)

        if restored_metadata is not None:
            return restored_metadata

        return None