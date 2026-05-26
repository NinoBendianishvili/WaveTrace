import os
import platform
import subprocess
from pathlib import Path


class FileOpenService:
    def open_file(self, file_path):
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File does not exist: {file_path}")

        system = platform.system()

        if system == "Darwin":
            subprocess.Popen(["open", str(file_path)])

        elif system == "Windows":
            os.startfile(str(file_path))

        elif system == "Linux":
            subprocess.Popen(["xdg-open", str(file_path)])

        else:
            raise RuntimeError(f"Opening files is not supported on this OS: {system}")