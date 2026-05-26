from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ableton_vcs.config.theme import *


class TrackStatusPill(QLabel):
    COLORS = {
        "same": ("#1F7A4D", "#D7FFE8"),
        "different_version": ("#9A5A00", "#FFE2A8"),
        "only_left": ("#A65000", "#FFDDBA"),
        "only_right": ("#A65000", "#FFDDBA"),
        "missing": ("#3D3D3D", "#CFCFCF"),
    }

    def __init__(self, status, text):
        super().__init__(text)

        bg, fg = self.COLORS.get(status, ("#555555", "#FFFFFF"))

        self.setStyleSheet(
            f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border-radius: 8px;
                padding: 2px 7px;
                font-size: 9px;
                font-weight: 700;
            }}
            """
        )


class TrackCell(QFrame):
    def __init__(self, track_data, visual_status, status_text):
        super().__init__()

        self.setMinimumHeight(48)
        self.setMaximumHeight(58)

        border_color = self.border_for_status(visual_status)

        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 1px solid {border_color};
                border-radius: 10px;
            }}

            QLabel {{
                background: transparent;
                border: none;
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(9, 7, 9, 7)
        layout.setSpacing(2)

        top = QHBoxLayout()
        top.setSpacing(6)

        if not track_data.get("exists"):
            name = QLabel("Not present")
            name.setStyleSheet(
                f"color: {TEXT_SECONDARY}; font-size: 11px; font-weight: 700;"
            )
            pill = TrackStatusPill("missing", status_text)

            top.addWidget(name, 1)
            top.addWidget(pill)

            hint = QLabel("Only in other version")
            hint.setStyleSheet(
                f"color: {TEXT_SECONDARY}; font-size: 9px;"
            )

            layout.addLayout(top)
            layout.addWidget(hint)
            return

        name_text = track_data.get("track_name", "Untitled track")
        if len(name_text) > 34:
            name_text = name_text[:33] + "…"

        name = QLabel(name_text)
        name.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 11px; font-weight: 800;"
        )

        pill = TrackStatusPill(visual_status, status_text)

        top.addWidget(name, 1)
        top.addWidget(pill)

        track_type = QLabel(track_data.get("track_type", "Unknown"))
        track_type.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 9px;"
        )

        layout.addLayout(top)
        layout.addWidget(track_type)

    def border_for_status(self, status):
        if status == "same":
            return "#2B7A50"

        if status == "different_version":
            return "#A86B16"

        if status in ["only_left", "only_right"]:
            return "#A65000"

        if status == "missing":
            return "#4A4A4A"

        return BORDER


class MergeTrackRow(QFrame):
    def __init__(self, row):
        super().__init__()

        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: transparent;
                border: none;
            }}

            QLabel {{
                background: transparent;
                border: none;
            }}
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        left_status, left_text, right_status, right_text = self.status_for_sides(row)

        left_cell = TrackCell(
            row["left"],
            left_status,
            left_text
        )

        right_cell = TrackCell(
            row["right"],
            right_status,
            right_text
        )

        layout.addWidget(left_cell, 1)
        layout.addWidget(right_cell, 1)

    def status_for_sides(self, row):
        merge_status = row.get("merge_status")

        if merge_status == "same":
            return "same", "Same", "same", "Same"

        if merge_status == "different_version":
            return "different_version", "Changed", "different_version", "Changed"

        if merge_status == "only_left":
            return "only_left", "Only here", "missing", "Missing"

        if merge_status == "only_right":
            return "missing", "Missing", "only_right", "New here"

        return "missing", "Unknown", "missing", "Unknown"


class MergePlaceholder(QWidget):
    def __init__(self, left_commit, right_commit, comparison_rows):
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 16)
        root.setSpacing(8)

        title = QLabel("Merge track comparison")
        title.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 17px; font-weight: 800;"
        )

        subtitle = QLabel("Compare tracks in the two selected versions.")
        subtitle.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 11px;"
        )

        root.addWidget(title)
        root.addWidget(subtitle)

        header = QHBoxLayout()
        header.setContentsMargins(0, 4, 0, 2)
        header.setSpacing(8)

        left_header = self.header_label(left_commit.get("name", "Left version"))
        right_header = self.header_label(right_commit.get("name", "Right version"))

        header.addWidget(left_header, 1)
        header.addWidget(right_header, 1)

        header_widget = QWidget()
        header_widget.setLayout(header)
        root.addWidget(header_widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }

            QScrollBar:vertical {
                background: #2B2B2B;
                width: 8px;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical {
                background: #555555;
                min-height: 28px;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical:hover {
                background: #777777;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            """
        )

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(6)

        if comparison_rows:
            for row in comparison_rows:
                content_layout.addWidget(MergeTrackRow(row))
        else:
            empty = QLabel("No track information found for these commits.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(
                f"color: {TEXT_SECONDARY}; font-size: 12px;"
            )
            content_layout.addWidget(empty)

        content_layout.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

    def header_label(self, text):
        if len(text) > 36:
            text = text[:35] + "…"

        label = QLabel(text)
        label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: 11px;
                font-weight: 800;
                padding: 2px 4px;
                background: transparent;
                border: none;
            }}
            """
        )

        return label