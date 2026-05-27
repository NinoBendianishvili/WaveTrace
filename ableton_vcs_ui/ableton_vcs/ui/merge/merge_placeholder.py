from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ableton_vcs.config.theme import *


CHECKBOX_X = 4
CHECKBOX_WIDTH = 26
CONTENT_X = 36
INDENT_WIDTH = 26
ROW_HEIGHT = 44
ROW_GAP = 8
TOP_PADDING = 8
BOTTOM_PADDING = 18


class StatusPill(QLabel):
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
                border-radius: 7px;
                padding: 2px 7px;
                font-size: 9px;
                font-weight: 700;
            }}
            """
        )


class TickBox(QCheckBox):
    def __init__(self):
        super().__init__()

        self.setFixedSize(CHECKBOX_WIDTH, CHECKBOX_WIDTH)

        self.setStyleSheet(
            f"""
            QCheckBox {{
                background: transparent;
                border: none;
                spacing: 0px;
            }}

            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border-radius: 7px;
                border: 1px solid {TEXT_SECONDARY};
                background-color: transparent;
            }}

            QCheckBox::indicator:checked {{
                background-color: {ACCENT};
                border: 1px solid {ACCENT};
            }}

            QCheckBox::indicator:disabled {{
                border: 1px solid #555555;
                background-color: #333333;
            }}
            """
        )


class TrackCard(QFrame):
    def __init__(self, row, side):
        super().__init__()

        self.row = row
        self.side = side

        side_data = row.get(side, {})
        visual_status, status_text = self.side_status(row, side)
        border_color = self.border_for_status(visual_status)

        is_group = row.get("track_type") == "GroupTrack"
        bg = BG_MAIN if is_group else BG_PANEL

        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {bg};
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
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(1)

        top = QHBoxLayout()
        top.setSpacing(6)

        if not side_data.get("exists"):
            name_text = "Not present"
            type_text = "Only in other version"
        else:
            name_text = side_data.get("track_name", "Untitled track")
            type_text = side_data.get("track_type", "Unknown")

            if type_text == "GroupTrack":
                name_text = "▾ " + name_text

        if len(name_text) > 32:
            name_text = name_text[:31] + "…"

        name = QLabel(name_text)
        name.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 11px; font-weight: 800;"
        )

        pill = StatusPill(visual_status, status_text)

        top.addWidget(name, 1)
        top.addWidget(pill)

        track_type = QLabel(type_text)
        track_type.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 9px;"
        )

        layout.addLayout(top)
        layout.addWidget(track_type)

    def side_status(self, row, side):
        side_data = row.get(side, {})

        if not side_data.get("exists"):
            return "missing", "Missing"

        merge_status = row.get("merge_status")

        if merge_status == "same":
            return "same", "Same"

        if merge_status == "different_version":
            return "different_version", "Changed"

        if merge_status == "only_left":
            if side == "left":
                return "only_left", "Only here"
            return "missing", "Missing"

        if merge_status == "only_right":
            if side == "right":
                return "only_right", "New here"
            return "missing", "Missing"

        return "missing", "Unknown"

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


class MergeTreeCanvas(QWidget):
    def __init__(self, side, rows):
        super().__init__()

        self.side = side
        self.rows = rows

        self.row_by_id = {
            row["global_track_id"]: row
            for row in rows
        }

        self.children_by_parent = self.build_children_map(rows)
        self.ordered_items = self.build_ordered_items()

        self.checkboxes = {}
        self.cards = {}

        self.setMinimumHeight(self.calculate_height())
        self.setAutoFillBackground(False)

        self.build_widgets()

    def calculate_height(self):
        row_count = len(self.ordered_items)

        if row_count == 0:
            return 240

        return TOP_PADDING + row_count * ROW_HEIGHT + (row_count - 1) * ROW_GAP + BOTTOM_PADDING

    def build_widgets(self):
        for item in self.ordered_items:
            track_id = item["track_id"]
            row = self.row_by_id[track_id]

            checkbox = TickBox()
            checkbox.setParent(self)
            checkbox.setChecked(self.default_checked(row))

            if not row.get(self.side, {}).get("exists"):
                checkbox.setEnabled(False)

            checkbox.toggled.connect(
                lambda checked, tid=track_id: self.on_track_checked(tid, checked)
            )

            card = TrackCard(row, self.side)
            card.setParent(self)

            self.checkboxes[track_id] = checkbox
            self.cards[track_id] = card

        self.position_widgets()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.position_widgets()

    def position_widgets(self):
        content_width = max(220, self.width() - CONTENT_X - 8)

        for index, item in enumerate(self.ordered_items):
            track_id = item["track_id"]
            depth = item["depth"]

            y = TOP_PADDING + index * (ROW_HEIGHT + ROW_GAP)

            checkbox = self.checkboxes.get(track_id)
            card = self.cards.get(track_id)

            if checkbox:
                checkbox_y = y + int((ROW_HEIGHT - CHECKBOX_WIDTH) / 2) + 1
                checkbox.setGeometry(CHECKBOX_X, checkbox_y, CHECKBOX_WIDTH, CHECKBOX_WIDTH)

            if card:
                card_x = CONTENT_X + depth * INDENT_WIDTH
                card_width = max(120, content_width - depth * INDENT_WIDTH)
                card.setGeometry(card_x, y, card_width, ROW_HEIGHT)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor(BORDER), 1)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        for item in self.ordered_items:
            track_id = item["track_id"]
            row = self.row_by_id.get(track_id)

            if not row or row.get("track_type") != "GroupTrack":
                continue

            span = self.group_span(track_id)

            if span is None:
                continue

            start_index, end_index = span
            depth = item["depth"]

            y1 = TOP_PADDING + start_index * (ROW_HEIGHT + ROW_GAP) - 5
            y2 = TOP_PADDING + end_index * (ROW_HEIGHT + ROW_GAP) + ROW_HEIGHT + 5

            x = CONTENT_X + depth * INDENT_WIDTH - 9
            width = self.width() - x - 6

            rect = QRectF(x, y1, width, y2 - y1)
            painter.drawRoundedRect(rect, 13, 13)

    def group_span(self, group_id):
        descendant_ids = set(self.get_descendant_ids(group_id))
        ids = {group_id} | descendant_ids

        indices = [
            index
            for index, item in enumerate(self.ordered_items)
            if item["track_id"] in ids
        ]

        if not indices:
            return None

        return min(indices), max(indices)

    def build_children_map(self, rows):
        children_by_parent = {}

        for row in rows:
            track_id = row["global_track_id"]
            parent_id = row.get("parent_group_global_id")

            children_by_parent.setdefault(parent_id, [])
            children_by_parent.setdefault(track_id, [])
            children_by_parent[parent_id].append(track_id)

        return children_by_parent

    def build_ordered_items(self):
        ordered = []
        visited = set()

        def visit(track_id, depth):
            if track_id in visited:
                return

            visited.add(track_id)
            ordered.append(
                {
                    "track_id": track_id,
                    "depth": depth,
                }
            )

            children = self.children_by_parent.get(track_id, [])

            for child_id in self.sorted_track_ids(children):
                visit(child_id, depth + 1)

        roots = self.children_by_parent.get(None, [])

        for root_id in self.sorted_track_ids(roots):
            visit(root_id, 0)

        for track_id in self.sorted_track_ids(list(self.row_by_id.keys())):
            if track_id not in visited:
                visit(track_id, 0)

        return ordered

    def sorted_track_ids(self, track_ids):
        def sort_key(track_id):
            row = self.row_by_id.get(track_id, {})
            is_group = row.get("track_type") == "GroupTrack"
            name = row.get("track_name", "")
            return (0 if is_group else 1, name.lower())

        return sorted(track_ids, key=sort_key)

    def default_checked(self, row):
        if not row.get(self.side, {}).get("exists"):
            return False

        return row.get("merge_status") == "same"

    def on_track_checked(self, track_id, checked):
        row = self.row_by_id.get(track_id)

        if not row:
            return

        if row.get("track_type") != "GroupTrack":
            return

        for child_id in self.get_descendant_ids(track_id):
            checkbox = self.checkboxes.get(child_id)

            if checkbox and checkbox.isEnabled():
                checkbox.blockSignals(True)
                checkbox.setChecked(checked)
                checkbox.blockSignals(False)

    def get_descendant_ids(self, track_id):
        result = []

        def collect(parent_id):
            for child_id in self.children_by_parent.get(parent_id, []):
                result.append(child_id)
                collect(child_id)

        collect(track_id)

        return result

    def get_selected_tracks(self):
        selected = []

        for track_id, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                selected.append(track_id)

        return selected


class MergeColumn(QWidget):
    def __init__(self, side, rows, title):
        super().__init__()

        self.side = side
        self.rows = rows

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        checkbox_header_space = QWidget()
        checkbox_header_space.setFixedWidth(CONTENT_X)

        title_label = QLabel(title)
        title_label.setStyleSheet(
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

        header.addWidget(checkbox_header_space)
        header.addWidget(title_label, 1)

        header_widget = QWidget()
        header_widget.setLayout(header)
        root.addWidget(header_widget)

        self.canvas = MergeTreeCanvas(side, rows)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(self.canvas)
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

        root.addWidget(scroll, 1)

    def get_selected_tracks(self):
        return self.canvas.get_selected_tracks()


class MergePlaceholder(QWidget):
    def __init__(self, left_commit, right_commit, comparison_rows):
        super().__init__()

        self.left_commit = left_commit
        self.right_commit = right_commit
        self.comparison_rows = comparison_rows

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 16)
        root.setSpacing(8)

        title = QLabel("Merge track comparison")
        title.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 17px; font-weight: 800;"
        )

        subtitle = QLabel("Select tracks or groups from each version to include in the merge.")
        subtitle.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 11px;"
        )

        root.addWidget(title)
        root.addWidget(subtitle)

        columns = QHBoxLayout()
        columns.setContentsMargins(0, 4, 0, 0)
        columns.setSpacing(12)

        left_title = left_commit.get("name", "Left version")
        right_title = right_commit.get("name", "Right version")

        self.left_column = MergeColumn(
            side="left",
            rows=comparison_rows,
            title=left_title,
        )

        self.right_column = MergeColumn(
            side="right",
            rows=comparison_rows,
            title=right_title,
        )

        columns.addWidget(self.left_column, 1)
        columns.addWidget(self.right_column, 1)

        columns_widget = QWidget()
        columns_widget.setLayout(columns)

        root.addWidget(columns_widget, 1)

    def get_selected_tracks(self):
        return {
            "left": self.left_column.get_selected_tracks(),
            "right": self.right_column.get_selected_tracks(),
        }