from PySide6.QtWidgets import QMainWindow
from ableton_vcs.config.theme import BG_MAIN
from ableton_vcs.app.landing_page import LandingPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WaveTrace - Ableton Version Control System")
        self.resize(1660, 980)
        self.setMinimumSize(1300, 820)
        self.setStyleSheet(f"background-color: {BG_MAIN};")
        self.setCentralWidget(LandingPage())
