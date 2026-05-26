import json
from pathlib import Path


EMPTY_REPOSITORY_DATA = {
    "selected_branch": "MAIN",
    "selected_commit": "",
    "commits": []
}


class CommitRepository:
    def __init__(self, json_path=None, data=None):
        self.json_path = Path(json_path) if json_path is not None else None

        if data is not None:
            self.data = data
        elif self.json_path is not None:
            self.data = self.load_data()
        else:
            self.data = EMPTY_REPOSITORY_DATA.copy()

        self.refresh_from_data()

    def refresh_from_data(self):
        self.commits = self.data.get("commits", [])
        self.branch_label = self.data.get("selected_branch", "MAIN")

        self.commit_map = {
            commit["hash"]: commit
            for commit in self.commits
            if "hash" in commit
        }

        self.selected_commit_hash = self.data.get("selected_commit", "")

        if not self.selected_commit_hash and self.commits:
            self.selected_commit_hash = self.commits[0].get("hash", "")

    def load_data(self):
        if self.json_path is None:
            return EMPTY_REPOSITORY_DATA.copy()

        if not self.json_path.exists():
            return EMPTY_REPOSITORY_DATA.copy()

        with self.json_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def get_commit(self, commit_hash):
        return self.commit_map.get(commit_hash)

    def pending_commit(self):
        for commit in self.commits:
            if commit.get("is_pending"):
                return commit

        return None