from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


class AudioPlayerService(QObject):
    position_changed = Signal(int)
    duration_changed = Signal(int)
    playback_state_changed = Signal(object)
    error_changed = Signal(str)

    def __init__(self):
        super().__init__()

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(self.duration_changed)
        self.player.playbackStateChanged.connect(self.playback_state_changed)
        self.player.errorOccurred.connect(self._on_error)

    def load(self, audio_path: str | Path):
        path = Path(audio_path)

        if not path.exists():
            self.error_changed.emit(f"Audio file not found: {path}")
            return False

        self.player.setSource(QUrl.fromLocalFile(str(path)))
        return True

    def play(self):
        self.player.play()

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()

    def seek(self, position: int):
        self.player.setPosition(position)

    def is_playing(self):
        return self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def _on_error(self, error, error_string):
        if error_string:
            self.error_changed.emit(error_string)