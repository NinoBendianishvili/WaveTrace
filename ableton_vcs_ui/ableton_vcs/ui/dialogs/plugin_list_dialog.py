from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ableton_vcs.config.theme import *


class PluginListDialog(QDialog):
    def __init__(self, plugins, commit_name="", parent=None):
        super().__init__(parent)

        self.plugins = plugins or []
        self.commit_name = commit_name or "Selected commit"

        self.setWindowTitle("Third-party plugins")
        self.resize(720, 460)

        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {BG_MAIN};
                color: {TEXT_PRIMARY};
                font-family: Arial;
            }}

            QLabel {{
                color: {TEXT_PRIMARY};
                background: transparent;
            }}

            QTableWidget {{
                background-color: {BG_PANEL};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 12px;
                gridline-color: {BORDER};
                selection-background-color: {BG_ELEMENT_HOVER};
            }}

            QHeaderView::section {{
                background-color: {BG_ELEMENT};
                color: {TEXT_PRIMARY};
                border: none;
                padding: 8px;
                font-weight: 700;
            }}

            QPushButton {{
                background-color: {BG_ELEMENT};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 12px;
                padding: 8px 18px;
                font-weight: 700;
            }}

            QPushButton:hover {{
                background-color: {BG_ELEMENT_HOVER};
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        title = QLabel("Third-party plugins")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: 800; color: {TEXT_PRIMARY};"
        )

        subtitle = QLabel(
            f"{self.commit_name} · {len(self.plugins)} plugin instance(s) found"
        )
        subtitle.setStyleSheet(
            f"font-size: 12px; color: {TEXT_SECONDARY};"
        )

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            [
                "Track",
                "Track Type",
                "Plugin",
                "Format",
            ]
        )

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectItems)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setAlternatingRowColors(False)

        self.fill_table()

        copy_shortcut = QShortcut(QKeySequence.Copy, self.table)
        copy_shortcut.activated.connect(self.copy_selected_cells)

        button_row = QHBoxLayout()
        button_row.addStretch()

        copy_all_button = QPushButton("Copy All")
        copy_all_button.clicked.connect(self.copy_all_cells)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)

        button_row.addWidget(copy_all_button)
        button_row.addWidget(close_button)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.table, 1)
        layout.addLayout(button_row)

    def make_item(self, text):
        item = QTableWidgetItem(str(text or ""))
        item.setForeground(QBrush(QColor(TEXT_PRIMARY)))
        item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        return item

    def fill_table(self):
        self.table.setRowCount(len(self.plugins))

        for row_index, plugin in enumerate(self.plugins):
            self.table.setItem(
                row_index,
                0,
                self.make_item(plugin.get("track_name", "")),
            )
            self.table.setItem(
                row_index,
                1,
                self.make_item(plugin.get("track_type", "")),
            )
            self.table.setItem(
                row_index,
                2,
                self.make_item(plugin.get("plugin_name", "")),
            )
            self.table.setItem(
                row_index,
                3,
                self.make_item(plugin.get("plugin_format", "")),
            )

    def copy_selected_cells(self):
        selected_ranges = self.table.selectedRanges()

        if not selected_ranges:
            return

        copied_rows = []

        for selected_range in selected_ranges:
            for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
                copied_cells = []

                for column in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                    item = self.table.item(row, column)
                    copied_cells.append(item.text() if item else "")

                copied_rows.append("\t".join(copied_cells))

        QApplication.clipboard().setText("\n".join(copied_rows))

    def copy_all_cells(self):
        rows = []

        headers = []

        for column in range(self.table.columnCount()):
            header_item = self.table.horizontalHeaderItem(column)
            headers.append(header_item.text() if header_item else "")

        rows.append("\t".join(headers))

        for row in range(self.table.rowCount()):
            cells = []

            for column in range(self.table.columnCount()):
                item = self.table.item(row, column)
                cells.append(item.text() if item else "")

            rows.append("\t".join(cells))

        QApplication.clipboard().setText("\n".join(rows))