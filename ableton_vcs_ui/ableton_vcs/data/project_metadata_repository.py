import json
import uuid
from pathlib import Path
from datetime import datetime

from ableton_vcs.config.app_paths import PROJECT_METADATA_DIR, ensure_app_data_files


class ProjectMetadataRepository:
    def __init__(self):
        ensure_app_data_files()

    def make_project_id(self):
        return uuid.uuid4().hex[:16]

    def get_metadata_path(self, project_id):
        return PROJECT_METADATA_DIR / f"{project_id}.json"

    def create_project_metadata(
        self,
        project_path,
        first_commit_name,
        first_commit_comment,
        audio_path,
        git_commit_hash,
        project_id
    ):
        project_path = Path(project_path).resolve()
        metadata_path = self.get_metadata_path(project_id)

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        commit_hash = git_commit_hash[:8] if git_commit_hash else "initial"

        data = {
            "project_id": project_id,
            "project_name": project_path.name,
            "last_known_path": str(project_path),
            "metadata_path": str(metadata_path),
            "created_at": now,
            "git_initialized": True,
            "branch_label": "MAIN",
            "selected_commit": commit_hash,
            "commits": [
                {
                    "hash": commit_hash,
                    "git_hash": git_commit_hash,
                    "name": first_commit_name,
                    "date": now,
                    "comment": first_commit_comment,
                    "audio_path": audio_path,
                    "predecessors": [],
                    "successors": [],
                    "lane": 0,
                    "y": 360
                }
            ]
        }

        with metadata_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        return data

    def load_by_project_id(self, project_id):
        metadata_path = self.get_metadata_path(project_id)

        if not metadata_path.exists():
            return None

        with metadata_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def save_metadata(self, metadata):
        project_id = metadata.get("project_id")

        if not project_id:
            raise ValueError("Cannot save metadata without project_id.")

        metadata_path = self.get_metadata_path(project_id)

        with metadata_path.open("w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=4)

    def update_last_known_path(self, project_id, project_path):
        metadata = self.load_by_project_id(project_id)

        if metadata is None:
            return None

        metadata["last_known_path"] = str(Path(project_path).resolve())
        self.save_metadata(metadata)

        return metadata

    def load_from_project_folder(self, project_path):
        project_path = Path(project_path).resolve()
        link_file = project_path / ".wavetrace" / "project.json"

        if not link_file.exists():
            return None

        with link_file.open("r", encoding="utf-8") as file:
            link_data = json.load(file)

        project_id = link_data.get("project_id")

        if not project_id:
            return None

        metadata = self.load_by_project_id(project_id)

        if metadata is None:
            return None

        metadata["last_known_path"] = str(project_path)
        self.save_metadata(metadata)

        return metadata