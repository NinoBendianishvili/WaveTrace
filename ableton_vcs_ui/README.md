# Ableton VCS UI Skeleton

This is the same PySide6 UI split into a cleaner folder structure.

## Run

```bash
cd ableton_vcs_ui
python3 -m venv .venv
source .venv/bin/activate
pip install PySide6
python main.py
```

## Structure

- `config/` stores colors, paths, and constants.
- `data/` stores demo commit data and the temporary commit repository.
- `ui/` stores reusable widgets and screen sections.
- `app/` stores the top-level landing page and main window.
- `services/` is intentionally empty for now; this is where Git, ALS parsing, initialization, and audio snapshot logic should go next.
