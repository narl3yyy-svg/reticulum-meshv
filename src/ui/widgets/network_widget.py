"""Network visualization widget showing mesh topology."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QGroupBox, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QApplication, QMenu
)
from PyQt6.QtCore import Qt, QTimer
from src.config.theme import MeshTheme
from src.ui.widgets.common import EmptyState
import RNS


class NetworkWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.monitor = getattr(backend, 'network_monitor', None)
        self.rns_node = getattr(backend, 'rns_node', None)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Network")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {MeshTheme.TEXT}; background: transparent;")
        layout.addWidget(title)

        header = QHBoxLayout()
        self.status_label = QLabel("Monitoring mesh network...")
        self.status_label.setStyleSheet(f"color: {MeshTheme.TEXT_MUTED}; background: transparent;")
        header.addWidget(self.status_label)
        header.addStretch()

        refresh_btn = QPushButton("Refresh Now")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {MeshTheme.ACTION_PRIMARY}; color: white; border: none;
                border-radius: 12px; padding: 8px 18px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background-color: {MeshTheme.ACTION_PRIMARY_HOVER}; }}
        """)
        refresh_btn.clicked.connect(self._refresh)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        self.network_empty = EmptyState("N", "No peers discovered", "Your mesh network will be visible here")
        layout.addWidget(self.network_empty)

        def group_style():
            return f"""
                QGroupBox {{ color: {MeshTheme.TEXT_MUTED}; font-size: 12px;
                    border: 1px solid {MeshTheme.BORDER_CARD}; border-radius: 16px; margin-top: 20px;
                    padding: 16px; }}
                QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left;
                    padding: 4px 12px; color: {MeshTheme.TEXT_MUTED}; font-size: 12px; }}
            """

        # === Peers ===
        peer_group = QGroupBox("Discovered Peers")
        peer_group.setStyleSheet(group_style())
        peer_layout = QVBoxLayout()

        self.peer_tree = QTreeWidget()
        self.peer_tree.setHeaderLabels(["Name", "Full Hash", "Last Seen"])
        self.peer_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.peer_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.peer_tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.peer_tree.setAlternatingRowColors(True)
        self.peer_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.peer_tree.customContextMenuRequested.connect(self._peer_context_menu)
        self.peer_tree.setStyleSheet(f"""
            QTreeWidget {{ background: transparent; border: 1px solid {MeshTheme.BORDER_CARD}; border-radius: 12px; }}
            QTreeWidget::item {{ color: {MeshTheme.TEXT}; padding: 6px 8px; }}
            QTreeWidget::item:hover {{ background: {MeshTheme.SURFACE_VARIANT}; }}
            QHeaderView::section {{ background: {MeshTheme.SURFACE}; color: {MeshTheme.TEXT_MUTED};
                border: none; border-bottom: 1px solid {MeshTheme.BORDER}; padding: 6px 8px; font-weight: 600; font-size: 12px; }}
        """)
        peer_layout.addWidget(self.peer_tree)

        peer_group.setLayout(peer_layout)
        layout.addWidget(peer_group, 1)

        # === Interfaces ===
        iface_group = QGroupBox("Active Interfaces")
        iface_group.setStyleSheet(group_style())
        iface_layout = QVBoxLayout()

        self.iface_tree = QTreeWidget()
        self.iface_tree.setHeaderLabels(["Interface", "Type", "Status", "RX", "TX"])
        self.iface_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.iface_tree.setAlternatingRowColors(True)
        self.iface_tree.setStyleSheet(f"""
            QTreeWidget {{ background: transparent; border: 1px solid {MeshTheme.BORDER_CARD}; border-radius: 12px; }}
            QTreeWidget::item {{ color: {MeshTheme.TEXT}; padding: 6px 8px; }}
            QTreeWidget::item:hover {{ background: {MeshTheme.SURFACE_VARIANT}; }}
            QHeaderView::section {{ background: {MeshTheme.SURFACE}; color: {MeshTheme.TEXT_MUTED};
                border: none; border-bottom: 1px solid {MeshTheme.BORDER}; padding: 6px 8px; font-weight: 600; font-size: 12px; }}
        """)
        iface_layout.addWidget(self.iface_tree)

        iface_group.setLayout(iface_layout)
        layout.addWidget(iface_group, 1)

        # === Paths ===
        path_group = QGroupBox("Known Paths")
        path_group.setStyleSheet(group_style())
        path_layout = QVBoxLayout()

        self.path_text = QTextEdit()
        self.path_text.setReadOnly(True)
        self.path_text.setMaximumHeight(120)
        self.path_text.setStyleSheet(f"font-family: 'JetBrains Mono', monospace; color: {MeshTheme.TEXT}; background: {MeshTheme.SURFACE}; border: none; border-radius: 12px; padding: 10px; font-size: 12px;")
        path_layout.addWidget(self.path_text)

        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        self.timer = QTimer()
        self.timer.timeout.connect(self._refresh)
        self.timer.start(5000)

        self._refresh()

    def _refresh(self):
        peers = []
        interfaces = {}
        paths = {}

        if self.monitor:
            peers = self.monitor.get_peers()
            interfaces = self.monitor.get_interfaces()
            paths = self.monitor.get_paths()

        # Also try direct RNS interface scan
        if not interfaces:
            try:
                for iface in RNS.Reticulum.interfaces:
                    name = str(getattr(iface, "name", "unknown"))
                    interfaces[name] = {
                        "type": type(iface).__name__,
                        "online": getattr(iface, "online", False),
                        "bytes_in": getattr(iface, "bytes_in", 0),
                        "bytes_out": getattr(iface, "bytes_out", 0),
                    }
            except:
                pass

        # Peer tree
        self.peer_tree.clear()
        for p in peers:
            from src.ui.widgets.announces_widget import _decode_app_data
            name = _decode_app_data(p.get("app_data", ""))
            full_hash = p.get("hash", "")
            item = QTreeWidgetItem([
                name or p.get("hash_short", "Unknown"),
                full_hash,
                self._fmt_time(p.get("last_seen", 0)),
            ])
            self.peer_tree.addTopLevelItem(item)

        # Interface tree
        self.iface_tree.clear()
        for name, info in interfaces.items():
            online = info.get("online", False)
            status = "Online" if online else "Offline"
            item = QTreeWidgetItem([
                name,
                info.get("type", ""),
                status,
                self._fmt_bytes(info.get("bytes_in", 0)),
                self._fmt_bytes(info.get("bytes_out", 0)),
            ])
            if online:
                item.setForeground(2, Qt.GlobalColor.green)
            else:
                item.setForeground(2, Qt.GlobalColor.gray)
            self.iface_tree.addTopLevelItem(item)

        # Paths
        path_lines = []
        for dest, hops in paths.items():
            hops_str = f"{hops} hop{'s' if hops != 1 else ''}" if isinstance(hops, int) else str(len(hops))
            path_lines.append(f"{dest} -> {hops_str}")
        self.path_text.setPlainText("\n".join(path_lines) if path_lines else "No paths discovered yet")

        self.network_empty.setVisible(len(peers) == 0)
        self.status_label.setText(f"Monitoring -- {len(peers)} peers, {len(interfaces)} interfaces, {len(paths)} paths")

    def _peer_context_menu(self, pos):
        item = self.peer_tree.itemAt(pos)
        if not item:
            return
        full_hash = item.text(1)
        name = item.text(0)

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background-color: {MeshTheme.SURFACE}; border: 1px solid {MeshTheme.BORDER}; border-radius: 12px; padding: 4px; }}
            QMenu::item {{ padding: 8px 24px; border-radius: 8px; color: {MeshTheme.TEXT}; }}
            QMenu::item:selected {{ background-color: {MeshTheme.ACTION_PRIMARY}; color: white; }}
        """)
        copy_a = menu.addAction("Copy Full Hash")
        msg_a = menu.addAction("Message")
        file_a = menu.addAction("Send File")
        action = menu.exec(self.peer_tree.viewport().mapToGlobal(pos))
        if action == copy_a:
            QApplication.clipboard().setText(full_hash)
            sb = self._find_status_bar()
            if sb:
                sb.showMessage("Hash copied to clipboard", 3000)
        elif action == msg_a:
            win = self.window()
            if hasattr(win, '_switch_to'):
                win._switch_to(0)
            mw = getattr(win, 'messages_widget', None)
            if mw:
                mw.add_conversation(full_hash, name)
                mw._select_conversation(full_hash)
        elif action == file_a:
            win = self.window()
            if hasattr(win, '_switch_to'):
                win._switch_to(1)
            fw = getattr(win, 'file_widget', None)
            if fw and hasattr(fw, 'dest_input'):
                fw.dest_input.setText(full_hash)

    def _find_status_bar(self):
        p = self.parent()
        while p:
            if hasattr(p, 'statusBar'):
                return p.statusBar()
            p = p.parent()
        return None

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
