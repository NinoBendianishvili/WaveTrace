from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSlider, QToolButton, QVBoxLayout
from ableton_vcs.config.theme import *
from ableton_vcs.ui.commit_info.waveform_widget import WaveformWidget

class AudioPlayerCard(QFrame):
    def __init__(self):
        super().__init__()
        self.audio_path_label = QLabel("")
        self.audio_path_label.setWordWrap(True)
        self.audio_path_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        self.setStyleSheet(
            f"""
            QFrame {{ background-color: transparent; border: none; }}
            QLabel {{ color: {TEXT_SECONDARY}; font-size: 11px; }}
            QSlider::groove:horizontal {{ height: 4px; background: {BORDER}; border-radius: 2px; }}
            QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 2px; }}
            QSlider::handle:horizontal {{ background: {ACCENT}; width: 16px; height: 16px; margin: -6px 0; border-radius: 8px; }}
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        top = QHBoxLayout()
        top.setSpacing(16)
        self.play_button = QToolButton()
        self.play_button.setText("▶")
        self.play_button.setCursor(Qt.PointingHandCursor)
        self.play_button.setFixedSize(72, 72)
        self.play_button.setStyleSheet(f"QToolButton {{ background-color: {BG_ELEMENT}; border: 2px solid {TEXT_SECONDARY}; border-radius: 36px; color: {TEXT_PRIMARY}; font-size: 28px; }} QToolButton:hover {{ background-color: {BG_ELEMENT_HOVER}; }}")
        waveform = WaveformWidget()
        top.addWidget(self.play_button)
        top.addWidget(waveform, 1)
        bottom = QHBoxLayout()
        bottom.setContentsMargins(2, 0, 2, 0)
        start_label = QLabel("0:00")
        end_label = QLabel("0:45")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setValue(18)
        bottom.addWidget(start_label)
        bottom.addSpacing(10)
        bottom.addWidget(self.slider, 1)
        bottom.addSpacing(10)
        bottom.addWidget(end_label)
        layout.addLayout(top)
        layout.addLayout(bottom)
        layout.addWidget(self.audio_path_label)

    def set_audio_path(self, audio_path):
        self.audio_path_label.setText(audio_path)
