import subprocess
from pathlib import Path


class GitService:
    def run_git(self, project_path, args):
        project_path = Path(project_path)

        result = subprocess.run(
            ["git"] + args,
            cwd=str(project_path),
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())

        return result.stdout.strip()

    def init_repository(self, project_path):
        project_path = Path(project_path)

        if not (project_path / ".git").exists():
            self.run_git(project_path, ["init"])

    def create_initial_commit(self, project_path, message):
        project_path = Path(project_path)

        self.run_git(project_path, ["add", "."])

        status = self.run_git(project_path, ["status", "--porcelain"])

        if not status:
            return self.get_head_hash(project_path)

        self.run_git(
            project_path,
            [
                "-c", "user.name=WaveTrace",
                "-c", "user.email=wavetrace@local",
                "commit",
                "-m", message
            ]
        )

        return self.get_head_hash(project_path)

    def get_head_hash(self, project_path):
        try:
            return self.run_git(project_path, ["rev-parse", "HEAD"])
        except RuntimeError:
            return ""