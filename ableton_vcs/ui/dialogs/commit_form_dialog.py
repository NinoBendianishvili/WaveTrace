from pathlib import Path
from PySide6.QtWidgets import QDialog, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QVBoxLayout
from ableton_vcs.config.theme import *
from ableton_vcs.ui.common.pill_button import PillButton

class CommitFormDialog(QDialog):
    def __init__(self, title_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title_text)
        self.resize(560, 460)
        self.selected_wav_path = ""
        self.setStyleSheet(
            f"""
            QDialog {{ background-color: {BG_MAIN}; }}
            QLabel {{ color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 600; }}
            QLineEdit, QTextEdit {{
                background-color: {BG_ELEMENT};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 14px;
                padding: 12px;
                font-size: 13px;
            }}
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        title = QLabel(title_text)
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 24px; font-weight: 700;")
        layout.addWidget(title)
        layout.addWidget(QLabel("Version name"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Comment"))
        self.comment_input = QTextEdit()
        self.comment_input.setMinimumHeight(160)
        layout.addWidget(self.comment_input)
        layout.addWidget(QLabel("Upload wav"))
        wav_row = QHBoxLayout()
        wav_row.setSpacing(12)
        self.wav_input = QLineEdit()
        self.wav_input.setPlaceholderText("Select a .wav file")
        self.wav_input.setReadOnly(True)
        self.wav_browse_button = PillButton("Browse", compact=True)
        wav_row.addWidget(self.wav_input, 1)
        wav_row.addWidget(self.wav_browse_button)
        layout.addLayout(wav_row)
        buttons = QHBoxLayout()
        buttons.addStretch()
        self.close_button = PillButton("Close", compact=True)
        self.commit_button = PillButton("Commit", primary=True, compact=True)
        buttons.addWidget(self.close_button)
        buttons.addWidget(self.commit_button)
        layout.addLayout(buttons)
        self.close_button.clicked.connect(self.reject)
        self.commit_button.clicked.connect(self.accept)
        self.wav_browse_button.clicked.connect(self.browse_wav)

    def browse_wav(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select WAV File", str(Path.home()), "WAV Files (*.wav)")
        if file_path:
            self.selected_wav_path = file_path
            self.wav_input.setText(file_path)
