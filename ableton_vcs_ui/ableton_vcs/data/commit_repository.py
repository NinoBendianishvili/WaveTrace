import json
from pathlib import Path

from ableton_vcs.data.dummy_data import DUMMY_COMMITS

class CommitRepository:
    def __init__(self, json_path=None, data=None):
        self.json_path = Path(json_path) if json_path is not None else None
        if data is not None:
            self.data = data
        else:
            self.data = self.load_data()
        self.refresh_from_data()

    def refresh_from_data(self):
        self.commits = self.data["commits"]
        self.branch_label = self.data.get("branch_label", "MAIN")
        self.commit_map = {commit["hash"]: commit for commit in self.commits}
        self.selected_commit_hash = self.data.get("selected_commit", self.commits[0]["hash"] if self.commits else "")

    def pending_commit(self):
        for commit in self.commits:
            if commit.get("is_pending"):
                return commit
        return None

    def ensure_dummy_file(self):
        if self.json_path is not None and not self.json_path.exists():
            self.json_path.write_text(json.dumps(DUMMY_COMMITS, indent=4), encoding="utf-8")

    def load_data(self):
        self.ensure_dummy_file()
        with self.json_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def get_commit(self, commit_hash):
        return self.commit_map.get(commit_hash)
