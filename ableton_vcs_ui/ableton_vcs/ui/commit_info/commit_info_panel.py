from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget
from ableton_vcs.config.theme import *
from ableton_vcs.ui.common.glass_card import GlassCard
from ableton_vcs.ui.commit_info.info_row import InfoRow
from ableton_vcs.ui.commit_info.audio_player_card import AudioPlayerCard

class CommitInfoPanel(GlassCard):
    def __init__(self):
        super().__init__(radius=26, border_color=BORDER, bg_color=BG_PANEL)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        title = QLabel("Commit Info")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 24px; font-weight: 700;")
        title_wrap = QWidget()
        title_layout = QVBoxLayout(title_wrap)
        title_layout.setContentsMargins(28, 28, 28, 24)
        title_layout.addWidget(title)
        divider1 = QFrame()
        divider1.setFrameShape(QFrame.HLine)
        divider1.setStyleSheet(f"color: {BORDER}; background-color: {BORDER}; max-height: 1px;")
        info_wrap = QWidget()
        info_layout = QVBoxLayout(info_wrap)
        info_layout.setContentsMargins(28, 24, 28, 28)
        info_layout.setSpacing(26)
        self.hash_row = InfoRow("#", "Commit Hash")
        self.date_row = InfoRow("◫", "Date")
        self.name_row = InfoRow("⌁", "Version Name")
        self.comment_row = InfoRow("◔", "Comment")
        self.links_row = InfoRow("⇄", "Connections")
        info_layout.addWidget(self.hash_row)
        info_layout.addWidget(self.date_row)
        info_layout.addWidget(self.name_row)
        info_layout.addWidget(self.comment_row)
        info_layout.addWidget(self.links_row)
        info_layout.addStretch()
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.HLine)
        divider2.setStyleSheet(f"color: {BORDER}; background-color: {BORDER}; max-height: 1px;")
        player_wrap = QWidget()
        player_layout = QVBoxLayout(player_wrap)
        player_layout.setContentsMargins(28, 24, 28, 24)
        self.audio_player = AudioPlayerCard()
        player_layout.addWidget(self.audio_player)
        layout.addWidget(title_wrap)
        layout.addWidget(divider1)
        layout.addWidget(info_wrap, 1)
        layout.addWidget(divider2)
        layout.addWidget(player_wrap)

    def set_commit(self, commit):
        predecessors = ", ".join(commit["predecessors"]) if commit["predecessors"] else "none"
        successors = ", ".join(commit["successors"]) if commit["successors"] else "none"
        self.hash_row.set_value(commit["hash"])
        self.date_row.set_value(commit["date"])
        self.name_row.set_value(commit["name"])
        self.comment_row.set_value(commit["comment"])
        self.links_row.set_value(f"predecessors: {predecessors}\nsuccessors: {successors}")
        self.audio_player.set_audio_path(commit["audio_path"])

    def set_pending_commit(self, commit):
        self.set_commit(commit)
        self.comment_row.set_value(commit.get("comment", "Changes were made after the latest commit."))

    def set_merge_preview(self, first_commit, second_commit):
        self.hash_row.set_value(f"{first_commit['hash']}  +  {second_commit['hash']}")
        self.date_row.set_value(f"{first_commit['date']}\n{second_commit['date']}")
        self.name_row.set_value(f"{first_commit['name']}\n{second_commit['name']}")
        self.comment_row.set_value("Two commits selected for merge.")
        self.links_row.set_value("Preview only.")
        self.audio_player.set_audio_path(f"{first_commit['audio_path']}\n{second_commit['audio_path']}")
