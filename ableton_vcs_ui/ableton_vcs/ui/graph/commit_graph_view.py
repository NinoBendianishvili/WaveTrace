from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPainterPath
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsEllipseItem,
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsTextItem,
    QGraphicsView,
)

from ableton_vcs.config.theme import *
from ableton_vcs.ui.graph.commit_node_item import CommitNodeItem


class CommitGraphView(QGraphicsView):
    commit_selected = Signal(str)
    merge_selection_changed = Signal(list)
    pending_node_selected = Signal(bool)
    pending_node_action_requested = Signal()

    def __init__(self, repository):
        super().__init__()

        self.repository = repository
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.Antialiasing)
        self.setFrameShape(QFrame.NoFrame)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.setStyleSheet("""
            QGraphicsView {
                background: transparent;
                border: none;
            }

            QScrollBar:vertical {
                background: #2B2B2B;
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background: #555555;
                min-height: 30px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover {
                background: #777777;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar:horizontal {
                background: #2B2B2B;
                height: 10px;
                margin: 0px;
                border-radius: 5px;
            }

            QScrollBar::handle:horizontal {
                background: #555555;
                min-width: 30px;
                border-radius: 5px;
            }

            QScrollBar::handle:horizontal:hover {
                background: #777777;
            }

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

        self.setMinimumHeight(640)

        self.lane_positions = {}
        self.selected_hash = repository.selected_commit_hash
        self.node_items = {}
        self.merge_mode = False
        self.merge_selected_hashes = []
        self.has_pending_changes = False

        self.draw_graph()

    def set_repository(self, repository):
        self.repository = repository
        self.selected_hash = repository.selected_commit_hash
        self.merge_mode = False
        self.merge_selected_hashes = []
        self.has_pending_changes = False
        self.draw_graph()

    def set_pending_changes(self, has_pending_changes):
        self.has_pending_changes = bool(has_pending_changes)

        if not self.has_pending_changes and self.selected_hash == "__pending__":
            self.selected_hash = self.repository.selected_commit_hash

        self.draw_graph()

    def get_pending_base_hash(self):
        working_base_commit = self.repository.data.get("working_base_commit", "")

        if working_base_commit:
            return working_base_commit

        selected_commit = self.repository.data.get("selected_commit", "")

        if selected_commit:
            return selected_commit

        if self.repository.selected_commit_hash:
            return self.repository.selected_commit_hash

        if self.repository.commits:
            return self.repository.commits[-1].get("hash", "")

        return ""

    def graph_commits(self):
        commits = [dict(commit) for commit in self.repository.commits]

        if not self.has_pending_changes or not commits:
            return commits

        base_hash = self.get_pending_base_hash()

        if not base_hash:
            return commits

        base_commit = None

        for commit in commits:
            if commit.get("hash") == base_hash:
                base_commit = commit
                break

        if base_commit is None:
            return commits

        for commit in commits:
            if commit.get("hash") == base_hash:
                successors = list(commit.get("successors", []))

                if "__pending__" not in successors:
                    successors.append("__pending__")

                commit["successors"] = successors
                break

        pending_commit = {
            "hash": "__pending__",
            "name": "uncommitted changes",
            "date": "",
            "comment": "Current project contains changes that are not committed yet.",
            "audio_path": "",
            "predecessors": [base_hash],
            "successors": [],
            "lane": base_commit.get("lane", 0),
            "branch": base_commit.get("branch", "MAIN"),
            "is_pending": True,
        }

        commits.append(pending_commit)

        return commits

    def set_merge_mode(self, enabled):
        self.merge_mode = enabled
        self.merge_selected_hashes = []
        self.merge_selection_changed.emit(self.merge_selected_hashes[:])
        self.update_selected_style()

    def format_date_label(self, date_text):
        if not date_text:
            return ""

        date_part = date_text.split(" ")[0]
        parts = date_part.split("-")

        if len(parts) != 3:
            return date_part

        year, month, day = parts

        month_map = {
            "01": "Jan",
            "02": "Feb",
            "03": "Mar",
            "04": "Apr",
            "05": "May",
            "06": "Jun",
            "07": "Jul",
            "08": "Aug",
            "09": "Sep",
            "10": "Oct",
            "11": "Nov",
            "12": "Dec",
        }

        return f"{int(day)} {month_map.get(month, month)}\n{year}"

    def add_date_label(self, x, y, date_text):
        text_item = QGraphicsTextItem(self.format_date_label(date_text))
        text_item.setDefaultTextColor(QColor(TEXT_PRIMARY))
        text_item.setFont(QFont("Arial", 12))
        text_item.setPos(x, y - 22)
        self.scene().addItem(text_item)

    def add_dashed_guide(self, x1, y, x2):
        pen = QPen(QColor(BORDER), 1)
        pen.setStyle(Qt.DashLine)
        self.scene().addLine(x1, y, x2, y, pen)

    def add_name_label(self, x, y, commit):
        name = commit.get("name", "Untitled")
        branch = commit.get("branch", "MAIN")

        max_name_length = 26

        if len(name) > max_name_length:
            name = name[: max_name_length - 1] + "…"

        label = QGraphicsSimpleTextItem(name)
        label.setBrush(QColor(TEXT_PRIMARY))
        label.setFont(QFont("Arial", 10, QFont.Bold))
        label.setPos(x + 44, y - 14)
        self.scene().addItem(label)

        branch_text = branch if branch else "MAIN"

        max_branch_length = 28

        if len(branch_text) > max_branch_length:
            branch_text = branch_text[: max_branch_length - 1] + "…"

        branch_item = QGraphicsSimpleTextItem(branch_text)
        branch_item.setFont(QFont("Arial", 8, QFont.Bold))

        if commit.get("is_pending"):
            branch_item.setBrush(QColor(RED))
        elif branch_text == "MAIN":
            branch_item.setBrush(QColor(TEXT_SECONDARY))
        else:
            branch_item.setBrush(QColor(BRANCH_ALT))

        branch_item.setPos(x + 44, y + 8)
        self.scene().addItem(branch_item)

    def calculate_layout(self):
        commits = self.graph_commits()

        if not commits:
            self.lane_positions = {}
            return {}

        commit_map = {
            commit["hash"]: commit
            for commit in commits
            if "hash" in commit
        }

        children = {
            commit["hash"]: [
                successor_hash
                for successor_hash in commit.get("successors", [])
                if successor_hash in commit_map
            ]
            for commit in commits
            if "hash" in commit
        }

        roots = [
            commit
            for commit in commits
            if not commit.get("predecessors")
        ]

        if not roots:
            roots = [commits[0]]

        depth_by_hash = {}
        lane_by_hash = {}
        next_lane = 1

        def assign(commit_hash, depth, lane):
            nonlocal next_lane

            if commit_hash in depth_by_hash:
                return

            depth_by_hash[commit_hash] = depth
            lane_by_hash[commit_hash] = lane

            commit = commit_map[commit_hash]
            commit_children = children.get(commit_hash, [])

            if not commit_children:
                return

            same_branch_children = []
            different_branch_children = []

            current_branch = commit.get("branch", "MAIN")

            for child_hash in commit_children:
                child = commit_map[child_hash]
                child_branch = child.get("branch", "MAIN")

                if child_branch == current_branch:
                    same_branch_children.append(child_hash)
                else:
                    different_branch_children.append(child_hash)

            ordered_children = same_branch_children + different_branch_children

            for index, child_hash in enumerate(ordered_children):
                child_branch = commit_map[child_hash].get("branch", "MAIN")

                if index == 0 and child_branch == current_branch:
                    child_lane = lane
                else:
                    if child_hash in lane_by_hash:
                        child_lane = lane_by_hash[child_hash]
                    else:
                        child_lane = next_lane
                        next_lane += 1

                assign(child_hash, depth + 1, child_lane)

        for root in roots:
            assign(root["hash"], 0, 0)

        for commit in commits:
            commit_hash = commit["hash"]

            if commit_hash not in depth_by_hash:
                depth_by_hash[commit_hash] = len(depth_by_hash)
                lane_by_hash[commit_hash] = next_lane
                next_lane += 1

        main_x = 330
        lane_gap = 270

        self.lane_positions = {
            lane: main_x + lane * lane_gap
            for lane in sorted(set(lane_by_hash.values()))
        }

        bottom_y = 540
        vertical_gap = 135
        top_padding = 100

        positioned_commits = {}

        for commit in commits:
            commit_hash = commit["hash"]
            depth = depth_by_hash[commit_hash]
            lane = lane_by_hash[commit_hash]

            x = self.lane_positions[lane]
            y = bottom_y - depth * vertical_gap

            positioned_commit = dict(commit)
            positioned_commit["lane"] = lane
            positioned_commit["y"] = y

            positioned_commits[commit_hash] = positioned_commit

        min_y = min(commit["y"] for commit in positioned_commits.values())

        if min_y < top_padding:
            shift_down = top_padding - min_y

            for commit in positioned_commits.values():
                commit["y"] += shift_down

        return positioned_commits

    def draw_connection(self, predecessor, successor):
        predecessor_x = self.lane_positions[predecessor["lane"]]
        successor_x = self.lane_positions[successor["lane"]]

        predecessor_y = predecessor["y"]
        successor_y = successor["y"]

        if predecessor.get("is_pending") or successor.get("is_pending"):
            color = RED
        else:
            color = (
                BRANCH_ALT
                if predecessor["lane"] != successor["lane"] or successor["lane"] != 0
                else BRANCH_MAIN
            )

        if predecessor_x == successor_x:
            pen = QPen(QColor(color), 3)
            pen.setCapStyle(Qt.RoundCap)
            self.scene().addLine(
                predecessor_x,
                predecessor_y,
                successor_x,
                successor_y,
                pen,
            )
            return

        path = QPainterPath(QPointF(predecessor_x, predecessor_y))

        mid_x = (predecessor_x + successor_x) / 2

        path.cubicTo(
            QPointF(mid_x, predecessor_y),
            QPointF(mid_x, successor_y),
            QPointF(successor_x, successor_y),
        )

        item = QGraphicsPathItem(path)

        pen = QPen(QColor(color), 3)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)

        item.setPen(pen)
        self.scene().addItem(item)

    def update_selected_style(self):
        for commit_hash, items in self.node_items.items():
            outer = items["outer"]
            inner = items["inner"]
            lane = items["lane"]
            is_pending = items["is_pending"]

            lane_color = RED if is_pending else (BRANCH_MAIN if lane == 0 else BRANCH_ALT)

            if self.merge_mode and commit_hash in self.merge_selected_hashes:
                outer.setPen(QPen(QColor(SELECTED), 3.6))
                inner.setBrush(QBrush(QColor(SELECTED)))

            elif commit_hash == self.selected_hash and not self.merge_mode:
                outer.setPen(QPen(QColor(SELECTED), 3.2))
                inner.setBrush(QBrush(QColor(SELECTED)))

            else:
                outer.setPen(QPen(QColor(lane_color), 2.4))
                inner.setBrush(QBrush(QColor(lane_color)))

    def on_node_click(self, commit_hash):
        if commit_hash == "__pending__":
            if self.merge_mode:
                return

            self.selected_hash = commit_hash
            self.update_selected_style()
            self.pending_node_selected.emit(True)
            self.pending_node_action_requested.emit()
            return

        if self.merge_mode:
            if commit_hash in self.merge_selected_hashes:
                self.merge_selected_hashes.remove(commit_hash)

            elif len(self.merge_selected_hashes) < 2:
                self.merge_selected_hashes.append(commit_hash)

            self.merge_selection_changed.emit(self.merge_selected_hashes[:])
            self.update_selected_style()
            return

        self.selected_hash = commit_hash

        self.update_selected_style()

        self.pending_node_selected.emit(False)
        self.commit_selected.emit(commit_hash)

    def draw_graph(self):
        scene = self.scene()
        scene.clear()

        self.node_items = {}

        positioned_commits = self.calculate_layout()

        if not positioned_commits:
            scene.setSceneRect(0, 0, 1200, 900)
            return

        date_x = 28
        main_x = self.lane_positions.get(0, 330)

        dated_commits = [
            commit
            for commit in positioned_commits.values()
            if commit["lane"] == 0 and commit.get("date")
        ]

        shown_days = []

        for commit in sorted(dated_commits, key=lambda item: item["y"]):
            date_label = commit["date"].split(" ")[0]

            if date_label not in shown_days:
                shown_days.append(date_label)
                self.add_date_label(date_x, commit["y"], date_label)
                self.add_dashed_guide(150, commit["y"], main_x - 24)

        for commit in positioned_commits.values():
            for successor_hash in commit.get("successors", []):
                successor = positioned_commits.get(successor_hash)

                if successor:
                    self.draw_connection(commit, successor)

        for commit in positioned_commits.values():
            x = self.lane_positions[commit["lane"]]
            y = commit["y"]

            lane_color = (
                RED
                if commit.get("is_pending")
                else (BRANCH_MAIN if commit["lane"] == 0 else BRANCH_ALT)
            )

            glow_target = QGraphicsEllipseItem(QRectF(x - 17, y - 17, 34, 34))
            glow_target.setPen(Qt.NoPen)
            glow_target.setBrush(Qt.NoBrush)

            glow = QGraphicsDropShadowEffect()
            glow.setBlurRadius(12)
            glow.setOffset(0, 0)
            glow.setColor(QColor(lane_color))

            glow_target.setGraphicsEffect(glow)
            glow_target.setOpacity(0.0)

            scene.addItem(glow_target)

            outer = scene.addEllipse(
                x - 17,
                y - 17,
                34,
                34,
                QPen(QColor(lane_color), 2.4),
                QBrush(QColor(BG_MAIN)),
            )

            inner = CommitNodeItem(
                commit,
                11,
                lane_color,
                lane_color,
                self.on_node_click,
            )

            inner.setPos(x, y)
            scene.addItem(inner)

            self.node_items[commit["hash"]] = {
                "outer": outer,
                "inner": inner,
                "lane": commit["lane"],
                "is_pending": commit.get("is_pending", False),
            }

            self.add_name_label(x, y, commit)

        self.update_selected_style()

        self.pending_node_selected.emit(self.selected_hash == "__pending__")

        max_lane = max(self.lane_positions.keys()) if self.lane_positions else 0
        scene_width = max(1200, self.lane_positions.get(max_lane, 330) + 520)

        min_y = min(commit["y"] for commit in positioned_commits.values())
        max_y = max(commit["y"] for commit in positioned_commits.values())

        scene_top = min(0, min_y - 180)
        scene_height = max(900, max_y - scene_top + 260)

        scene.setSceneRect(0, scene_top, scene_width, scene_height)