import json
from pathlib import Path


APP_DATA_DIR = Path.home() / ".wavetrace"
RECENT_PROJECTS_FILE = APP_DATA_DIR / "recent_projects.json"

# Used only to migrate older WaveTrace projects that stored full metadata
# outside the Ableton project folder.
LEGACY_PROJECT_METADATA_DIR = APP_DATA_DIR / "projects"

# Backup mirror of project-local metadata.
# This is not the main source of truth. It is only used for recovery.
PROJECT_METADATA_BACKUP_DIR = APP_DATA_DIR / "backups"
PROJECT_METADATA_BACKUP_INDEX_FILE = PROJECT_METADATA_BACKUP_DIR / "index.json"


DEFAULT_RECENT_PROJECTS_DATA = {
    "schema_version": 1,
    "last_opened_project": "",
    "last_opened_project_id": "",
    "projects": [],
}


DEFAULT_BACKUP_INDEX_DATA = {
    "schema_version": 1,
    "projects": {}
}


def ensure_app_data_files():
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROJECT_METADATA_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if not RECENT_PROJECTS_FILE.exists():
        with RECENT_PROJECTS_FILE.open("w", encoding="utf-8") as file:
            json.dump(DEFAULT_RECENT_PROJECTS_DATA, file, indent=4)

    if not PROJECT_METADATA_BACKUP_INDEX_FILE.exists():
        with PROJECT_METADATA_BACKUP_INDEX_FILE.open("w", encoding="utf-8") as file:
            json.dump(DEFAULT_BACKUP_INDEX_DATA, file, indent=4)