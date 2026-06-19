"""Network visualization widget showing mesh topology."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QGroupBox, QTreeWidget, QTreeWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer
from src.config.theme import MeshTheme
from src.ui.widgets.common import StatusDot, EmptyState


class NetworkWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.monitor = backend.network_monitor
        self.rns_node = backend.rns_node

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Network Visualizer")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {MeshTheme.TEXT}; background: transparent;")
        layout.addWidget(title)

        header = QHBoxLayout()
        self.status_label = QLabel("Monitoring mesh network...")
        self.status_label.setStyleSheet(f"color: {MeshTheme.TEXT_MUTED}; background: transparent;")
        header.addWidget(self.status_label)
        header.addStretch()

        refresh_btn = QPushButton("Refresh Now")
        refresh_btn.clicked.connect(self._refresh)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        self.network_empty = EmptyState("\U0001F310", "No peers discovered", "Your mesh network will be visible here")
        layout.addWidget(self.network_empty)

        peer_group = QGroupBox("Discovered Peers")
        peer_group.setStyleSheet(f"""
            QGroupBox {{ color: {MeshTheme.TEXT_MUTED}; font-size: 12px;
                border: 1px solid {MeshTheme.BORDER}; border-radius: 10px; margin-top: 20px;
                padding: 16px; }}
            QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left;
                padding: 4px 12px; color: {MeshTheme.TEXT_MUTED}; font-size: 12px; }}
        """)
        peer_layout = QVBoxLayout()

        self.peer_tree = QTreeWidget()
        self.peer_tree.setHeaderLabels(["Peer", "Hash", "Last Seen"])
        self.peer_tree.header().setStretchLastSection(True)
        self.peer_tree.setAlternatingRowColors(True)
        self.peer_tree.setStyleSheet(f"""
            QTreeWidget {{ background: transparent; border: 1px solid {MeshTheme.BORDER}; border-radius: 8px; }}
            QTreeWidget::item {{ color: {MeshTheme.TEXT}; padding: 4px 8px; }}
            QTreeWidget::item:hover {{ background: {MeshTheme.SURFACE_VARIANT}; }}
            QHeaderView::section {{ background: {MeshTheme.SURFACE}; color: {MeshTheme.TEXT_MUTED};
                border: none; border-bottom: 1px solid {MeshTheme.BORDER}; padding: 6px 8px; font-weight: 600; }}
        """)
        peer_layout.addWidget(self.peer_tree)

        peer_group.setLayout(peer_layout)
        layout.addWidget(peer_group)

        iface_group = QGroupBox("Active Interfaces")
        iface_group.setStyleSheet(f"""
            QGroupBox {{ color: {MeshTheme.TEXT_MUTED}; font-size: 12px;
                border: 1px solid {MeshTheme.BORDER}; border-radius: 10px; margin-top: 20px;
                padding: 16px; }}
            QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left;
                padding: 4px 12px; color: {MeshTheme.TEXT_MUTED}; font-size: 12px; }}
        """)
        iface_layout = QVBoxLayout()

        self.iface_tree = QTreeWidget()
        self.iface_tree.setHeaderLabels(["Interface", "Type", "Status", "RX", "TX"])
        self.iface_tree.header().setStretchLastSection(True)
        self.iface_tree.setAlternatingRowColors(True)
        self.iface_tree.setStyleSheet(f"""
            QTreeWidget {{ background: transparent; border: 1px solid {MeshTheme.BORDER}; border-radius: 8px; }}
            QTreeWidget::item {{ color: {MeshTheme.TEXT}; padding: 4px 8px; }}
            QTreeWidget::item:hover {{ background: {MeshTheme.SURFACE_VARIANT}; }}
            QHeaderView::section {{ background: {MeshTheme.SURFACE}; color: {MeshTheme.TEXT_MUTED};
                border: none; border-bottom: 1px solid {MeshTheme.BORDER}; padding: 6px 8px; font-weight: 600; }}
        """)
        iface_layout.addWidget(self.iface_tree)

        iface_group.setLayout(iface_layout)
        layout.addWidget(iface_group)

        path_group = QGroupBox("Known Paths")
        path_group.setStyleSheet(f"""
            QGroupBox {{ color: {MeshTheme.TEXT_MUTED}; font-size: 12px;
                border: 1px solid {MeshTheme.BORDER}; border-radius: 10px; margin-top: 20px;
                padding: 16px; }}
            QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left;
                padding: 4px 12px; color: {MeshTheme.TEXT_MUTED}; font-size: 12px; }}
        """)
        path_layout = QVBoxLayout()

        self.path_text = QTextEdit()
        self.path_text.setReadOnly(True)
        self.path_text.setMaximumHeight(120)
        self.path_text.setStyleSheet(f"font-family: 'JetBrains Mono', monospace; color: {MeshTheme.TEXT}; background: {MeshTheme.SURFACE_VARIANT}; border: none; border-radius: 8px; padding: 8px;")
        path_layout.addWidget(self.path_text)

        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        self.timer = QTimer()
        self.timer.timeout.connect(self._refresh)
        self.timer.start(10000)

        self._refresh()

    def _refresh(self):
        if not self.monitor:
            return

        peers = self.monitor.get_peers()
        interfaces = self.monitor.get_interfaces()
        paths = self.monitor.get_paths()

        self.peer_tree.clear()
        for p in peers:
            item = QTreeWidgetItem([
                p.get("app_data", p.get("hash_short", "Unknown")),
                p.get("hash", "")[:16] + "...",
                self._fmt_time(p.get("last_seen", 0)),
            ])
            self.peer_tree.addTopLevelItem(item)

        self.iface_tree.clear()
        for name, info in interfaces.items():
            online = info.get("online", False)
            dot_color = MeshTheme.SUCCESS if online else MeshTheme.TEXT_DIM
            status = f"● {'Online' if online else 'Offline'}"
            item = QTreeWidgetItem([
                name,
                info.get("type", ""),
                status,
                self._fmt_bytes(info.get("bytes_in", 0)),
                self._fmt_bytes(info.get("bytes_out", 0)),
            ])
            item.setForeground(2, Qt.GlobalColor.green if online else Qt.GlobalColor.gray)
            self.iface_tree.addTopLevelItem(item)

        path_lines = []
        for dest, hops in paths.items():
            hops_str = f"{hops} hop{'s' if hops != 1 else ''}" if isinstance(hops, int) else str(len(hops))
            path_lines.append(f"{dest[:16]}... → {hops_str}")
        self.path_text.setPlainText("\n".join(path_lines) if path_lines else "No paths discovered yet")

        self.network_empty.setVisible(len(peers) == 0)
        self.status_label.setText(f"Monitoring — {len(peers)} peers, {len(interfaces)} interfaces, {len(paths)} paths")

    def _fmt_time(self, ts: float) -> str:
        if not ts:
            return ""
        from datetime import datetime
        return datetime.fromtimestamp(ts).strftime("%H:%M:%S")

    def _fmt_bytes(self, b: int) -> str:
        if b < 1024:
            return f"{b}B"
        elif b < 1024 * 1024:
            return f"{b/1024:.1f}KB"
        else:
            return f"{b/(1024*1024):.1f}MB"
