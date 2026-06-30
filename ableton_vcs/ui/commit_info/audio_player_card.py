from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QToolButton, QVBoxLayout

from ableton_vcs.config.theme import *
from ableton_vcs.ui.commit_info.waveform_widget import WaveformWidget


class AudioPlayerCard(QFrame):
    def __init__(self):
        super().__init__()

        self.project_path = ""
        self.audio_path = ""
        self.resolved_audio_path = None
        self.duration_ms = 0

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)

        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.85)

        self.audio_path_label = QLabel("No WAV snapshot attached to this commit.")
        self.audio_path_label.setWordWrap(True)
        self.audio_path_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 10px;"
        )

        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: transparent;
                border: none;
            }}

            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: 10px;
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        player_row = QHBoxLayout()
        player_row.setSpacing(12)

        self.play_button = QToolButton()
        self.play_button.setText("▶")
        self.play_button.setCursor(Qt.PointingHandCursor)
        self.play_button.setFixedSize(54, 54)
        self.play_button.setEnabled(False)
        self.play_button.setStyleSheet(
            f"""
            QToolButton {{
                background-color: {BG_ELEMENT};
                border: 2px solid {TEXT_SECONDARY};
                border-radius: 27px;
                color: {TEXT_PRIMARY};
                font-size: 22px;
            }}

            QToolButton:hover {{
                background-color: {BG_ELEMENT_HOVER};
            }}

            QToolButton:disabled {{
                color: {TEXT_SECONDARY};
                border-color: {BORDER};
            }}
            """
        )

        self.waveform = WaveformWidget()

        player_row.addWidget(self.play_button)
        player_row.addWidget(self.waveform, 1)

        time_row = QHBoxLayout()
        time_row.setContentsMargins(66, 0, 0, 0)

        self.start_label = QLabel("0:00")
        self.end_label = QLabel("0:00")

        self.start_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 10px;"
        )
        self.end_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 10px;"
        )

        time_row.addWidget(self.start_label)
        time_row.addStretch()
        time_row.addWidget(self.end_label)

        path_row = QHBoxLayout()
        path_row.setContentsMargins(66, 0, 0, 0)
        path_row.addWidget(self.audio_path_label)

        layout.addLayout(player_row)
        layout.addLayout(time_row)
        layout.addLayout(path_row)

        self.play_button.clicked.connect(self.toggle_playback)
        self.waveform.seek_requested.connect(self.handle_waveform_seek)

        self.player.durationChanged.connect(self.handle_duration_changed)
        self.player.positionChanged.connect(self.handle_position_changed)
        self.player.playbackStateChanged.connect(self.handle_playback_state_changed)
        self.player.errorOccurred.connect(self.handle_player_error)

    def set_project_path(self, project_path):
        self.project_path = str(project_path) if project_path else ""
        self.reload_source()

    def set_audio_path(self, audio_path, project_path=None):
        if project_path is not None:
            self.project_path = str(project_path) if project_path else ""

        self.audio_path = str(audio_path or "").strip()
        self.reload_source()

    def reload_source(self):
        self.player.stop()
        self.player.setSource(QUrl())

        self.play_button.setText("▶")
        self.duration_ms = 0

        self.waveform.set_progress(0.0)
        self.waveform.set_seek_enabled(False)

        self.start_label.setText("0:00")
        self.end_label.setText("0:00")

        self.resolved_audio_path = self.resolve_audio_path(self.audio_path)

        if not self.audio_path:
            self.audio_path_label.setText("No WAV snapshot attached to this commit.")
            self.play_button.setEnabled(False)
            return

        self.audio_path_label.setText(self.display_audio_directory(self.audio_path))

        if self.resolved_audio_path is None:
            self.play_button.setEnabled(False)
            return

        self.player.setSource(QUrl.fromLocalFile(str(self.resolved_audio_path)))

        self.play_button.setEnabled(True)
        self.waveform.set_seek_enabled(True)

    def resolve_audio_path(self, audio_path):
        if not audio_path:
            return None

        path = Path(audio_path).expanduser()

        if path.is_absolute():
            return path if path.exists() else None

        if self.project_path:
            candidate = Path(self.project_path).expanduser().resolve() / path

            if candidate.exists():
                return candidate

        if path.exists():
            return path.resolve()

        return None

    def display_audio_directory(self, audio_path):
        if not audio_path:
            return ""

        path = Path(audio_path)

        if path.parent == Path("."):
            return ""

        return str(path.parent)

    def toggle_playback(self):
        if self.resolved_audio_path is None:
            return

        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def handle_waveform_seek(self, progress):
        if self.duration_ms <= 0:
            return

        position = int(self.duration_ms * progress)
        self.player.setPosition(position)
        self.start_label.setText(self.format_time(position))

    def handle_duration_changed(self, duration):
        self.duration_ms = max(duration, 0)
        self.end_label.setText(self.format_time(self.duration_ms))

        self.waveform.set_seek_enabled(
            self.duration_ms > 0 and self.resolved_audio_path is not None
        )

    def handle_position_changed(self, position):
        self.start_label.setText(self.format_time(position))

        if self.duration_ms > 0:
            self.waveform.set_progress(position / self.duration_ms)
        else:
            self.waveform.set_progress(0.0)

    def handle_playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setText("Ⅱ")
        else:
            self.play_button.setText("▶")

    def handle_player_error(self, error, error_string):
        if error == QMediaPlayer.Error.NoError:
            return

        self.play_button.setEnabled(False)
        self.waveform.set_seek_enabled(False)

    def format_time(self, milliseconds):
        total_seconds = max(int(milliseconds / 1000), 0)
        minutes = total_seconds // 60
        seconds = total_seconds % 60

        return f"{minutes}:{seconds:02d}"