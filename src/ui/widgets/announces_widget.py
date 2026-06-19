"""Announces widget – see incoming Reticulum announces from other nodes."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QFrame, QGridLayout, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QDateTime
from PyQt6.QtGui import QFont, QColor
from src.config.theme import MeshTheme
import time


class AnnounceCard(QFrame):
    def __init__(self, peer_info, parent=None):
        super().__init__(parent)
        self.peer_info = peer_info
        self.setFixedSize(280, 170)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {MeshTheme.SURFACE};
                border: 1px solid {MeshTheme.BORDER};
                border-radius: 12px;
            }}
            QFrame:hover {{
                border: 1px solid {MeshTheme.ACCENT}60;
                background-color: {MeshTheme.SURFACE_VARIANT};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(6)

        hash_str = peer_info.get('hash', '')
        short_hash = peer_info.get('hash_short', hash_str[:12])
        app_data = peer_info.get('app_data', '')

        avatar = QLabel(short_hash[0].upper())
        avatar.setFixedSize(44, 44)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            background-color: {MeshTheme.ACCENT}30;
            color: {MeshTheme.ACCENT}; font-size: 20px; font-weight: 700;
            border-radius: 22px;
        """)
        layout.addWidget(avatar, 0, Qt.AlignmentFlag.AlignCenter)

        name = app_data if app_data else short_hash
        name_label = QLabel(name[:24])
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {MeshTheme.TEXT}; background: transparent;")
        layout.addWidget(name_label)

        hash_label = QLabel(short_hash)
        hash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hash_label.setStyleSheet(f"font-family: 'JetBrains Mono', monospace; font-size: 10px; color: {MeshTheme.TEXT_DIM}; background: transparent;")
        layout.addWidget(hash_label)

        now = time.time()
        last_seen = peer_info.get('last_seen', 0)
        delta = now - last_seen
        if delta < 60:
            status_text = "Just now"
            color = MeshTheme.SUCCESS
        elif delta < 300:
            status_text = f"{int(delta//60)}m ago"
            color = MeshTheme.SUCCESS
        elif delta < 3600:
            status_text = f"{int(delta//60)}m ago"
            color = MeshTheme.WARNING
        else:
            status_text = f"{int(delta//3600)}h ago"
            color = MeshTheme.TEXT_DIM

        status_label = QLabel(f"\u25CF {status_text}")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet(f"font-size: 11px; color: {color}; background: transparent;")
        layout.addWidget(status_label)

        first_seen = peer_info.get('first_seen', 0)
        if first_seen:
            fs_label = QLabel(f"Known since {QDateTime.fromSecsSinceEpoch(int(first_seen)).toString('MMM d, HH:mm')}")
            fs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fs_label.setStyleSheet(f"font-size: 10px; color: {MeshTheme.TEXT_DIM}; background: transparent;")
            layout.addWidget(fs_label)


class AnnouncesWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.network_monitor = backend.network_monitor

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QWidget()
        hdr_layout = QHBoxLayout(header)
        hdr_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Network Announces")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {MeshTheme.TEXT}; background: transparent;")
        hdr_layout.addWidget(title)

        self.count_label = QLabel("0 peers")
        self.count_label.setStyleSheet(f"font-size: 13px; color: {MeshTheme.TEXT_MUTED}; background: transparent; padding: 4px 0;")
        hdr_layout.addWidget(self.count_label)

        hdr_layout.addStretch()

        announce_btn = QPushButton("Announce Myself")
        announce_btn.setFixedHeight(36)
        announce_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MeshTheme.ACCENT}; color: white; border: none;
                border-radius: 8px; padding: 6px 18px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {MeshTheme.ACCENT_DARK}; }}
        """)
        announce_btn.clicked.connect(self._announce_myself)
        hdr_layout.addWidget(announce_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedHeight(36)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; color: {MeshTheme.TEXT_MUTED};
                border: 1px solid {MeshTheme.BORDER}; border-radius: 8px;
                padding: 6px 18px; font-size: 13px;
            }}
            QPushButton:hover {{ background-color: {MeshTheme.SURFACE_VARIANT}; color: {MeshTheme.TEXT}; }}
        """)
        refresh_btn.clicked.connect(self._refresh)
        hdr_layout.addWidget(refresh_btn)

        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(container)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(16)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        self.timer = QTimer()
        self.timer.timeout.connect(self._refresh)
        self.timer.start(15000)

        self._refresh()

    def _refresh(self):
        if not self.network_monitor:
            return
        peers = self.network_monitor.get_peers()
        peers.sort(key=lambda p: p.get('last_seen', 0), reverse=True)

        self.count_label.setText(f"{len(peers)} peer{'s' if len(peers) != 1 else ''}")

        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w:
                w.deleteLater()

        for idx, peer in enumerate(peers):
            card = AnnounceCard(peer)
            row = idx // 4
            col = idx % 4
            self.grid.addWidget(card, row, col)

    def _announce_myself(self):
        if self.backend.lxmf_messenger:
            self.backend.lxmf_messenger.announce()
        elif self.backend.rns_node:
            self.backend.rns_node.announce_myself()
        if hasattr(self, 'statusBar') and callable(self.statusBar):
            self.statusBar().showMessage("Announced on network", 3000)
        else:
            p = self.parent()
            while p:
                if hasattr(p, 'statusBar'):
                    p.statusBar().showMessage("Announced on network", 3000)
                    break
                p = p.parent()
