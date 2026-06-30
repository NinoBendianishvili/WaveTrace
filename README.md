# WaveTrace

WaveTrace is a desktop application for Git-based version management of Ableton Live project folders. It provides a graphical interface for creating versions, browsing commit history, switching between versions, attaching audio previews, and merging track-level changes in Ableton Live projects.

## Features

- Initialize an Ableton Live project as a WaveTrace project
- Create Git-based project versions through a graphical interface
- Browse project history using a commit graph
- Attach audio preview files to commits
- Open previous commits and continue work from older versions
- Create new branches from older commits
- Merge two project versions using Ableton track metadata
- Store WaveTrace metadata in a portable project-local format

## Download macOS app

A packaged macOS `.dmg` version of WaveTrace is available from the repository's GitHub Releases page:

https://github.com/NinoBendianishvili/WaveTrace/releases

Download the latest `WaveTrace.dmg`, open it, and drag `WaveTrace.app` into the Applications folder.

Because the application is not signed with an Apple Developer certificate, macOS may show a security warning. In that case, right-click the app and choose **Open**.

## Requirements

- Python 3
- Git
- PySide6
- Ableton Live project folder containing an `.als` file

## Run from source

Clone the repository:

```bash
git clone https://github.com/NinoBendianishvili/WaveTrace.git
cd WaveTrace
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install PySide6
```

Run the application:

```bash
python main.py
```

## Project structure

```text
WaveTrace/
├── ableton_vcs/
│   ├── app/
│   ├── config/
│   ├── data/
│   ├── resources/
│   ├── services/
│   └── ui/
├── main.py
├── README.md
└── wavetrace_symbol_icon_black_transparent.icns
```

## Metadata storage

WaveTrace stores the main project metadata inside the selected Ableton project folder:

```text
Ableton Project Folder/
├── .git/
└── .wavetrace/
    ├── project.json
    └── audio/
```

`project.json` is the main source of truth for WaveTrace metadata. It stores the project ID, branches, commits, selected commit, selected branch, track maps, comments, and references to attached audio previews.

Audio previews are copied into:

```text
.wavetrace/audio/
```

and are stored using relative paths in the commit metadata.

WaveTrace also stores local application data in the user's home directory:

```text
~/.wavetrace/
├── recent_projects.json
└── backups/
    ├── index.json
    └── <project_id>/
        └── project.json
```

`recent_projects.json` is machine-specific and is used only to display recently opened projects. Backup metadata is used only for recovery if the project-local `.wavetrace/project.json` file is missing or corrupted.

## Git usage

WaveTrace uses Git as the technical backend, but users do not need to type Git commands manually. Git operations are accessed through the WaveTrace interface.

WaveTrace is mainly designed for local version management and portable project folders. Git remote operations such as `push` and `pull` are technically possible because the project is Git-based, but they are not the recommended sharing method for Ableton projects. To transfer a project, share the complete Ableton project folder including hidden `.git` and `.wavetrace` directories.

## Notes

- Ableton audio samples are not duplicated into every version.
- Audio previews must currently be exported manually from Ableton and attached in WaveTrace.
- The packaged `.dmg` file is not stored in the source repository. It is uploaded separately through GitHub Releases.

