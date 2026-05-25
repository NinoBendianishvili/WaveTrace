from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPainterPath
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsTextItem, QGraphicsView
from ableton_vcs.config.theme import *
from ableton_vcs.ui.graph.commit_node_item import CommitNodeItem

class CommitGraphView(QGraphicsView):
    commit_selected = Signal(str)
    merge_selection_changed = Signal(list)
    pending_node_selected = Signal(bool)

    def __init__(self, repository):
        super().__init__()
        self.repository = repository
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.Antialiasing)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("background: transparent;")
        self.setMinimumHeight(640)
        self.lane_positions = {0: 330, 1: 670, 2: 850}
        self.selected_hash = repository.selected_commit_hash
        self.node_items = {}
        self.merge_mode = False
        self.merge_selected_hashes = []
        self.draw_graph()

    def set_repository(self, repository):
        self.repository = repository
        self.selected_hash = repository.selected_commit_hash
        self.merge_mode = False
        self.merge_selected_hashes = []
        self.draw_graph()

    def format_date_label(self, date_text):
        year, month, day = date_text.split("-")
        month_map = {"01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun", "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"}
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

    def add_name_label(self, x, y, text):
        label = QGraphicsSimpleTextItem(text)
        label.setBrush(QColor(TEXT_PRIMARY))
        label.setFont(QFont("Arial", 10))
        label.setPos(x + 44, y - 10)
        self.scene().addItem(label)

    def draw_connection(self, predecessor, successor):
        predecessor_x = self.lane_positions[predecessor["lane"]]
        successor_x = self.lane_positions[successor["lane"]]
        predecessor_y = predecessor["y"]
        successor_y = successor["y"]
        if predecessor.get("is_pending") or successor.get("is_pending"):
            color = RED
        else:
            color = BRANCH_ALT if predecessor["lane"] != successor["lane"] or successor["lane"] != 0 else BRANCH_MAIN
        if predecessor_x == successor_x:
            pen = QPen(QColor(color), 3)
            pen.setCapStyle(Qt.RoundCap)
            self.scene().addLine(predecessor_x, predecessor_y, successor_x, successor_y, pen)
            return
        path = QPainterPath(QPointF(predecessor_x, predecessor_y))
        control_offset = abs(successor_x - predecessor_x) * 0.55
        path.cubicTo(QPointF(predecessor_x + control_offset, predecessor_y), QPointF(successor_x - control_offset, successor_y), QPointF(successor_x, successor_y))
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

    def set_merge_mode(self, enabled):
        self.merge_mode = enabled
        self.merge_selected_hashes = []
        self.merge_selection_changed.emit(self.merge_selected_hashes[:])
        self.update_selected_style()

    def on_node_click(self, commit_hash):
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
        selected_commit = self.repository.get_commit(commit_hash)
        self.pending_node_selected.emit(bool(selected_commit and selected_commit.get("is_pending")))
        self.commit_selected.emit(commit_hash)

    def draw_graph(self):
        scene = self.scene()
        scene.clear()
        self.node_items = {}
        date_x = 28
        main_x = self.lane_positions[0]
        dated_commits = [commit for commit in self.repository.commits if commit["lane"] == 0 and commit["date"]]
        shown_days = []
        for commit in sorted(dated_commits, key=lambda item: item["y"]):
            date_label = commit["date"].split(" ")[0]
            if date_label not in shown_days:
                shown_days.append(date_label)
                self.add_date_label(date_x, commit["y"], date_label)
                self.add_dashed_guide(150, commit["y"], main_x - 24)
        for commit in self.repository.commits:
            for successor_hash in commit["successors"]:
                successor = self.repository.get_commit(successor_hash)
                if successor:
                    self.draw_connection(commit, successor)
        for commit in self.repository.commits:
            x = self.lane_positions[commit["lane"]]
            y = commit["y"]
            lane_color = RED if commit.get("is_pending") else (BRANCH_MAIN if commit["lane"] == 0 else BRANCH_ALT)
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
            outer = scene.addEllipse(x - 17, y - 17, 34, 34, QPen(QColor(lane_color), 2.4), QBrush(QColor(BG_MAIN)))
            inner = CommitNodeItem(commit, 11, lane_color, lane_color, self.on_node_click)
            inner.setPos(x, y)
            scene.addItem(inner)
            self.node_items[commit["hash"]] = {"outer": outer, "inner": inner, "lane": commit["lane"], "is_pending": commit.get("is_pending", False)}
            self.add_name_label(x, y, commit["name"])
        self.update_selected_style()
        current_commit = self.repository.get_commit(self.selected_hash)
        self.pending_node_selected.emit(bool(current_commit and current_commit.get("is_pending")))
        scene.setSceneRect(0, 0, 980, 760)
