import json
from datetime import datetime
from pathlib import Path

from ableton_vcs.data.recent_projects_repository import RecentProjectsRepository
from ableton_vcs.data.project_metadata_repository import ProjectMetadataRepository
from ableton_vcs.services.git_service import GitService
from ableton_vcs.services.als_track_service import AlsTrackService
from ableton_vcs.services.track_id_service import TrackIdService
from ableton_vcs.services.file_open_service import FileOpenService
from ableton_vcs.services.merge_track_service import MergeTrackService
from ableton_vcs.services.audio_snapshot_service import AudioSnapshotService


class ProjectService:
    def __init__(self):
        self.recent_projects_repository = RecentProjectsRepository()
        self.project_metadata_repository = ProjectMetadataRepository()
        self.git_service = GitService()
        self.als_track_service = AlsTrackService()
        self.track_id_service = TrackIdService()
        self.file_open_service = FileOpenService()
        self.merge_track_service = MergeTrackService()
        self.audio_snapshot_service = AudioSnapshotService()

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

    def has_uncommitted_changes(self, project_path):
        project_path = Path(project_path).resolve()

        if not self.has_git_repository(project_path):
            return False

        return self.git_service.has_uncommitted_changes(project_path)

    def discard_uncommitted_changes(self, project_path):
        project_path = Path(project_path).resolve()

        if not self.has_git_repository(project_path):
            raise RuntimeError("This project is not a Git repository.")

        self.git_service.discard_uncommitted_changes(project_path)

    def initialize_project(self, project_path, first_commit_name, first_commit_comment, audio_path):
        project_path = Path(project_path).resolve()

        if not self.git_service.is_git_available():
            raise RuntimeError("Git is not installed or not available on this computer.")

        wavetrace_dir = project_path / ".wavetrace"
        wavetrace_dir.mkdir(parents=True, exist_ok=True)

        self.ensure_project_gitignore(project_path)

        self.git_service.init_repository(project_path)

        project_id = self.project_metadata_repository.make_project_id()

        link_data = {
            "project_id": project_id,
            "project_name": project_path.name,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        link_file = wavetrace_dir / "project.json"

        with link_file.open("w", encoding="utf-8") as file:
            json.dump(link_data, file, indent=4)

        metadata = self.project_metadata_repository.create_empty_project_metadata(
            project_path=project_path,
            project_id=project_id,
        )

        metadata = self.create_commit(
            project_path=project_path,
            name=first_commit_name,
            comment=first_commit_comment,
            audio_path=audio_path,
            metadata=metadata,
        )

        self.remember_project(project_path)

        return metadata

    def get_commit_by_hash(self, metadata, commit_hash):
        for commit in metadata.get("commits", []):
            if commit.get("hash") == commit_hash:
                return commit

        return None

    def resolve_commit_als_path(self, project_path, commit):
        project_path = Path(project_path).resolve()

        saved_als_path = commit.get("als_path", "")

        if saved_als_path:
            saved_als_path = Path(saved_als_path)
            candidate = project_path / saved_als_path.name

            if candidate.exists():
                return candidate

            if saved_als_path.exists():
                return saved_als_path

        als_files = sorted(project_path.glob("*.als"))

        if not als_files:
            raise FileNotFoundError("No .als file found after checking out this commit.")

        return als_files[0]

    def open_commit_version(self, project_path, commit_hash):
        project_path = Path(project_path).resolve()
        metadata = self.load_project_metadata(project_path)

        if metadata is None:
            raise RuntimeError("Project metadata could not be loaded.")

        commit = self.get_commit_by_hash(metadata, commit_hash)

        if not commit:
            raise RuntimeError("Selected commit could not be found in metadata.")

        git_hash = commit.get("git_hash")

        if not git_hash:
            raise RuntimeError("Selected commit does not have a Git hash.")

        if self.git_service.has_uncommitted_changes(project_path):
            raise RuntimeError(
                "This project has uncommitted changes. Please commit or discard them before opening another version."
            )

        commit_branch = commit.get("branch", "MAIN")
        metadata.setdefault("branches", {})

        branch_head = metadata["branches"].get(commit_branch)

        if commit_hash == branch_head:
            self.git_service.switch_branch(project_path, commit_branch)

            metadata["selected_branch"] = commit_branch
            metadata["working_base_commit"] = ""
            metadata["working_mode"] = "normal"
            metadata["selected_commit"] = commit["hash"]

        else:
            self.git_service.checkout_commit_detached(project_path, git_hash)

            metadata["selected_branch"] = commit_branch
            metadata["working_base_commit"] = commit["hash"]
            metadata["working_mode"] = "detached_experiment"
            metadata["selected_commit"] = commit["hash"]

        self.project_metadata_repository.save_metadata(metadata)

        als_path = self.resolve_commit_als_path(project_path, commit)
        self.file_open_service.open_file(als_path)

        return str(als_path)

    def create_commit(self, project_path, name, comment, audio_path="", metadata=None, branch_name=None):
        project_path = Path(project_path).resolve()

        if metadata is None:
            metadata = self.load_project_metadata(project_path)

        if metadata is None:
            raise RuntimeError("Project metadata could not be loaded.")

        working_base_commit_hash = metadata.get("working_base_commit", "")
        working_mode = metadata.get("working_mode", "normal")

        if working_mode == "detached_experiment":
            if not branch_name:
                raise RuntimeError("Branch name is required when committing from an older version.")

            self.git_service.create_branch_from_current_head(project_path, branch_name)

            metadata["selected_branch"] = branch_name
            metadata.setdefault("branches", {})
            metadata["branches"][branch_name] = working_base_commit_hash

            parent_commit = self.get_commit_by_hash(metadata, working_base_commit_hash)

            if parent_commit is None:
                raise RuntimeError("Working base commit could not be found.")

        else:
            selected_commit_hash = metadata.get("selected_commit", "")
            parent_commit = self.get_commit_by_hash(metadata, selected_commit_hash)

            if parent_commit is None and metadata.get("commits"):
                parent_commit = metadata["commits"][-1]

        extracted_data = self.als_track_service.extract_current_project_tracks(project_path)

        previous_track_map = parent_commit["track_map"] if parent_commit else {}

        updated_track_data = self.track_id_service.build_track_map_for_commit(
            current_tracks=extracted_data["tracks"],
            previous_track_map=previous_track_map,
            global_track_id_counter=metadata.get("global_track_id_counter", 0),
        )

        self.ensure_project_gitignore(project_path)

        git_commit_hash = self.git_service.create_commit(
            project_path=project_path,
            message=name,
        )

        short_hash = git_commit_hash[:8] if git_commit_hash else f"commit{len(metadata['commits']) + 1}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        stored_audio_path = self.audio_snapshot_service.save_commit_audio(
            project_path=project_path,
            source_audio_path=audio_path,
            commit_hash=short_hash,
        )

        previous_commit_hash = parent_commit["hash"] if parent_commit else None
        parent_lane = parent_commit.get("lane", 0) if parent_commit else 0
        is_branch_commit = working_mode == "detached_experiment"

        commit_data = {
            "hash": short_hash,
            "git_hash": git_commit_hash,
            "name": name,
            "date": now,
            "comment": comment,
            "audio_path": stored_audio_path,
            "predecessors": [previous_commit_hash] if previous_commit_hash else [],
            "successors": [],
            "lane": parent_lane + 1 if is_branch_commit else parent_lane,
            "y": max(360 - len(metadata["commits"]) * 120, 40),

            "branch": metadata.get("selected_branch", "MAIN"),
            "als_path": extracted_data["als_path"],
            "global_track_id_counter": updated_track_data["global_track_id_counter"],
            "track_map": updated_track_data["track_map"],
        }

        if previous_commit_hash:
            parent_commit.setdefault("successors", [])

            if short_hash not in parent_commit["successors"]:
                parent_commit["successors"].append(short_hash)

        metadata["working_base_commit"] = ""
        metadata["working_mode"] = "normal"

        metadata = self.project_metadata_repository.append_commit(
            metadata=metadata,
            commit_data=commit_data,
        )

        return metadata

    def load_project_metadata(self, project_path):
        return self.project_metadata_repository.load_from_project_folder(project_path)

    def compare_commits_for_merge(self, left_commit, right_commit):
        return self.merge_track_service.compare_track_maps(
            left_commit=left_commit,
            right_commit=right_commit
        )

    def ensure_project_gitignore(self, project_path):
        project_path = Path(project_path).resolve()
        gitignore_path = project_path / ".gitignore"

        ignore_lines = [
            "Samples/",
            ".wavetrace/audio/",
            "*.asd",
            ".DS_Store",
        ]

        if gitignore_path.exists():
            content = gitignore_path.read_text(encoding="utf-8")
        else:
            content = ""

        existing_lines = set(line.strip() for line in content.splitlines())

        changed = False

        for line in ignore_lines:
            if line not in existing_lines:
                if content and not content.endswith("\n"):
                    content += "\n"

                content += f"{line}\n"
                changed = True

        if changed:
            gitignore_path.write_text(content, encoding="utf-8")

    def reopen_current_working_als(self, project_path):
        project_path = Path(project_path).resolve()

        metadata = self.load_project_metadata(project_path)

        if metadata is None:
            raise RuntimeError("Project metadata could not be loaded.")

        selected_commit_hash = metadata.get("selected_commit", "")

        if not selected_commit_hash:
            raise RuntimeError("No selected commit found.")

        commit = self.get_commit_by_hash(metadata, selected_commit_hash)

        if commit is None:
            raise RuntimeError("Selected commit could not be found.")

        als_path = self.resolve_commit_als_path(project_path, commit)

        self.file_open_service.open_file(als_path)

        return str(als_path)