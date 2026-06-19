"""Shared UI components."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from src.config.theme import MeshTheme


class EmptyState(QWidget):
    def __init__(self, icon: str, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"font-size: 48px; color: {MeshTheme.TEXT_DIM}; background: transparent;")
        layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {MeshTheme.TEXT_MUTED}; background: transparent;")
        layout.addWidget(title_label)

        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sub_label.setStyleSheet(f"font-size: 12px; color: {MeshTheme.TEXT_DIM}; background: transparent;")
            layout.addWidget(sub_label)

        self.setStyleSheet("background: transparent;")


class StatusDot(QWidget):
    ONLINE = "#4ade80"
    OFFLINE = "#71717a"
    AWAY = "#fb923c"
    UNKNOWN = "#3f3f46"

    def __init__(self, color: str = UNKNOWN, size: int = 10, parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(size, size)

    def set_color(self, color: str):
        self._color = color
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor, QBrush
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor(self._color)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())
