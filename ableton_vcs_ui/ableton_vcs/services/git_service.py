import subprocess
from pathlib import Path


class GitService:
    def is_git_available(self):
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def run_git(self, project_path, args):
        project_path = Path(project_path)

        result = subprocess.run(
            ["git"] + args,
            cwd=str(project_path),
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())

        return result.stdout.strip()

    def run_git_allow_failure(self, project_path, args):
        project_path = Path(project_path)

        result = subprocess.run(
            ["git"] + args,
            cwd=str(project_path),
            capture_output=True,
            text=True,
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }

    def init_repository(self, project_path):
        project_path = Path(project_path)

        if not (project_path / ".git").exists():
            self.run_git(project_path, ["init"])

    def has_uncommitted_changes(self, project_path):
        status = self.run_git(
            project_path,
            ["status", "--porcelain", "--untracked-files=no"],
        )

        return bool(status.strip())

    def discard_uncommitted_changes(self, project_path):
        self.run_git(project_path, ["reset", "--hard", "HEAD"])

    def checkout_commit_detached(self, project_path, git_hash):
        if not git_hash:
            raise RuntimeError("Selected commit does not have a Git hash.")

        self.run_git(project_path, ["checkout", "--detach", git_hash])

    def switch_branch(self, project_path, branch_name):
        if not branch_name:
            raise RuntimeError("Branch name cannot be empty.")

        self.run_git(project_path, ["switch", branch_name])

    def create_branch_from_current_head(self, project_path, branch_name):
        if not branch_name:
            raise RuntimeError("Branch name cannot be empty.")

        self.run_git(project_path, ["switch", "-c", branch_name])

    def create_commit(self, project_path, message):
        project_path = Path(project_path)

        self.run_git(project_path, ["add", "."])

        status = self.run_git(
            project_path,
            ["status", "--porcelain", "--untracked-files=no"],
        )

        if not status:
            raise RuntimeError("There are no project changes to commit.")

        self.run_git(
            project_path,
            [
                "-c",
                "user.name=WaveTrace",
                "-c",
                "user.email=wavetrace@local",
                "commit",
                "-m",
                message,
            ],
        )

        return self.get_head_hash(project_path)

    def merge_no_commit_allow_conflicts(self, project_path, other_git_hash):
        if not other_git_hash:
            raise RuntimeError("Commit to merge is missing.")

        return self.run_git_allow_failure(
            project_path,
            ["merge", "--no-commit", other_git_hash],
        )

    def abort_merge(self, project_path):
        result = self.run_git_allow_failure(project_path, ["merge", "--abort"])
        return result["returncode"] == 0

    def commit_current_merge(self, project_path, message):
        self.run_git(project_path, ["add", "."])

        self.run_git(
            project_path,
            [
                "-c",
                "user.name=WaveTrace",
                "-c",
                "user.email=wavetrace@local",
                "commit",
                "-m",
                message,
            ],
        )

        return self.get_head_hash(project_path)

    def get_file_from_commit(self, project_path, git_hash, repo_relative_path, output_path):
        project_path = Path(project_path)
        output_path = Path(output_path)

        result = subprocess.run(
            ["git", "show", f"{git_hash}:{repo_relative_path}"],
            cwd=str(project_path),
            capture_output=True,
        )

        if result.returncode != 0:
            error = result.stderr.decode("utf-8", errors="ignore").strip()
            raise RuntimeError(error or f"Could not read {repo_relative_path} from commit {git_hash}.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(result.stdout)

        return str(output_path)

    def get_head_hash(self, project_path):
        try:
            return self.run_git(project_path, ["rev-parse", "HEAD"])
        except RuntimeError:
            return ""

    def get_current_branch(self, project_path):
        try:
            return self.run_git(project_path, ["branch", "--show-current"])
        except RuntimeError:
            return ""