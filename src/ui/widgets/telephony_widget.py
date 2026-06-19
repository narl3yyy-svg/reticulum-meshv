"""Telephony tab — LXST voice calls (placeholder)."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from src.config.theme import MeshTheme
from src.ui.widgets.common import EmptyState


class TelephonyWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Telephony")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {MeshTheme.TEXT}; background: transparent;")
        layout.addWidget(title)

        empty = EmptyState("T", "No active calls", "LXST voice calls will appear here when available")
        layout.addWidget(empty, 1)
