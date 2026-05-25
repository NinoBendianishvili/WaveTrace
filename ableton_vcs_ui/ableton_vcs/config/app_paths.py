import json
from pathlib import Path


APP_DATA_DIR = Path.home() / ".wavetrace"
RECENT_PROJECTS_FILE = APP_DATA_DIR / "recent_projects.json"
PROJECT_METADATA_DIR = APP_DATA_DIR / "projects"


DEFAULT_RECENT_PROJECTS_DATA = {
    "last_opened_project": "",
    "recent_projects": []
}


def ensure_app_data_files():
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROJECT_METADATA_DIR.mkdir(parents=True, exist_ok=True)

    if not RECENT_PROJECTS_FILE.exists():
        with RECENT_PROJECTS_FILE.open("w", encoding="utf-8") as file:
            json.dump(DEFAULT_RECENT_PROJECTS_DATA, file, indent=4)