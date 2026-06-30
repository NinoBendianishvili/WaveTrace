import shutil
from pathlib import Path


class AudioSnapshotService:
    def ensure_audio_dir(self, project_path):
        audio_dir = Path(project_path) / ".wavetrace" / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        return audio_dir

    def save_commit_audio(self, project_path, source_audio_path, commit_hash):
        if not source_audio_path:
            return ""

        project_path = Path(project_path).resolve()
        source_audio_path = Path(source_audio_path).resolve()

        if not source_audio_path.exists():
            raise FileNotFoundError(f"Selected WAV file does not exist: {source_audio_path}")

        if source_audio_path.suffix.lower() != ".wav":
            raise ValueError("Only .wav files are supported for commit audio snapshots.")

        audio_dir = self.ensure_audio_dir(project_path)

        short_hash = commit_hash[:8]
        destination = audio_dir / f"{short_hash}.wav"

        if source_audio_path != destination.resolve():
            shutil.copy2(source_audio_path, destination)

        return str(destination.relative_to(project_path))