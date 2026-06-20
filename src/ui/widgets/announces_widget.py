"""Announces widget — see incoming Reticulum announces from other nodes."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QFrame, QGridLayout, QApplication, QMenu
)
from PyQt6.QtCore import Qt, QTimer, QDateTime
from src.config.theme import MeshTheme
from src.ui.widgets.common import EmptyState
import time
import json


def _decode_app_data(app_data):
    """Decode app_data from announce, handling JSON, binary, and plain text."""
    if not app_data:
        return ""
    if isinstance(app_data, bytes):
        try:
            text = app_data.decode("utf-8", errors="replace")
        except:
            return app_data.hex()[:16]
    else:
        text = str(app_data)

    # MeshChatX sends JSON with display_name field
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data.get("display_name", data.get("name", text))
    except:
        pass

    # Strip non-printable characters
    cleaned = ""
    for ch in text:
        if ch.isprintable() or ch in (' ', '\t', '\n'):
            cleaned += ch
    return cleaned.strip() if cleaned.strip() else text[:16]


class AnnounceCard(QFrame):
    def __init__(self, peer_info, on_message=None, on_file=None, on_copy=None, parent=None):
        super().__init__(parent)
        self.peer_info = peer_info
        self._on_message = on_message
        self._on_file = on_file
        self._on_copy = on_copy
        self.setFixedSize(280, 200)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {MeshTheme.SURFACE};
                border: 1px solid {MeshTheme.BORDER_CARD};
                border-radius: 16px;
            }}
            QFrame:hover {{
                border: 1px solid {MeshTheme.ACCENT};
                background-color: {MeshTheme.SURFACE_VARIANT};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(6)

        hash_str = peer_info.get('hash', '')
        short_hash = peer_info.get('hash_short', hash_str[:12])
        app_data = peer_info.get('app_data', '')
        display_name = _decode_app_data(app_data)
        self._display_name = display_name
        self._hash = hash_str

        avatar = QLabel(display_name[0].upper() if display_name else '?')
        avatar.setFixedSize(44, 44)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            background-color: {MeshTheme.ACCENT}30;
            color: {MeshTheme.ACCENT}; font-size: 20px; font-weight: 700;
            border-radius: 22px;
        """)
        layout.addWidget(avatar, 0, Qt.AlignmentFlag.AlignCenter)

        name_label = QLabel(display_name[:24] if display_name else short_hash)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {MeshTheme.TEXT}; background: transparent;")
        layout.addWidget(name_label)

        hash_label = QLabel(short_hash)
        hash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hash_label.setCursor(Qt.CursorShape.PointingHandCursor)
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

        status_label = QLabel(status_text)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet(f"font-size: 11px; color: {color}; background: transparent;")
        layout.addWidget(status_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        msg_btn = QPushButton("Message")
        msg_btn.setFixedHeight(28)
        msg_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {MeshTheme.ACTION_PRIMARY}; color: white;
                border: none; border-radius: 8px; padding: 4px 12px; font-size: 11px; font-weight: 600; }}
            QPushButton:hover {{ background-color: {MeshTheme.ACTION_PRIMARY_HOVER}; }}
        """)
        msg_btn.clicked.connect(self._message)
        btn_row.addWidget(msg_btn)

        file_btn = QPushButton("Send File")
        file_btn.setFixedHeight(28)
        file_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {MeshTheme.ACCENT};
                border: 1px solid {MeshTheme.ACCENT}; border-radius: 8px; padding: 4px 12px; font-size: 11px; }}
            QPushButton:hover {{ background-color: {MeshTheme.ACCENT}20; }}
        """)
        file_btn.clicked.connect(self._send_file)
        btn_row.addWidget(file_btn)

        layout.addLayout(btn_row)

    def _message(self):
        if self._on_message:
            self._on_message(self._hash, self._display_name)

    def _send_file(self):
        if self._on_file:
            self._on_file(self._hash, self._display_name)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background-color: {MeshTheme.SURFACE}; border: 1px solid {MeshTheme.BORDER}; border-radius: 12px; padding: 4px; }}
            QMenu::item {{ padding: 8px 24px; border-radius: 8px; color: {MeshTheme.TEXT}; }}
            QMenu::item:selected {{ background-color: {MeshTheme.ACTION_PRIMARY}; color: white; }}
        """)
        copy_a = menu.addAction("Copy Hash")
        msg_a = menu.addAction("Message")
        file_a = menu.addAction("Send File")
        action = menu.exec(event.globalPos())
        if action == copy_a:
            QApplication.clipboard().setText(self._hash)
            if self._on_copy:
                self._on_copy()
        elif action == msg_a:
            self._message()
        elif action == file_a:
            self._send_file()


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
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {MeshTheme.TEXT}; background: transparent;")
        hdr_layout.addWidget(title)

        self.count_label = QLabel("0 peers")
        self.count_label.setStyleSheet(f"font-size: 13px; color: {MeshTheme.TEXT_MUTED}; background: transparent; padding: 4px 0;")
        hdr_layout.addWidget(self.count_label)

        hdr_layout.addStretch()

        announce_btn = QPushButton("Announce Myself")
        announce_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {MeshTheme.ACTION_PRIMARY}; color: white; border: none;
                border-radius: 12px; padding: 8px 18px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background-color: {MeshTheme.ACTION_PRIMARY_HOVER}; }}
        """)
        announce_btn.clicked.connect(self._announce_myself)
        hdr_layout.addWidget(announce_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {MeshTheme.TEXT_MUTED};
                border: 1px solid {MeshTheme.BORDER}; border-radius: 12px; padding: 8px 18px; font-size: 13px; }}
            QPushButton:hover {{ background-color: {MeshTheme.SURFACE_VARIANT}; color: {MeshTheme.TEXT}; }}
        """)
        refresh_btn.clicked.connect(self._refresh)
        hdr_layout.addWidget(refresh_btn)

        layout.addWidget(header)

        self.announces_empty = EmptyState("A", "No announces yet", "Network announces from other nodes appear here")
        layout.addWidget(self.announces_empty)

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
        self.timer.start(5000)

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
            card = AnnounceCard(
                peer,
                on_message=self._message_peer,
                on_file=self._file_peer,
                on_copy=self._copied
            )
            row = idx // 4
            col = idx % 4
            self.grid.addWidget(card, row, col)

        self.announces_empty.setVisible(len(peers) == 0)

    def _message_peer(self, hash_str, display_name):
        win = self.window()
        if hasattr(win, '_switch_to'):
            win._switch_to(0)
        mw = getattr(win, 'messages_widget', None)
        if mw:
            mw.add_conversation(hash_str, display_name or hash_str[:16])
            mw._select_conversation(hash_str)

    def _file_peer(self, hash_str, display_name):
        win = self.window()
        if hasattr(win, '_switch_to'):
            win._switch_to(1)
        fw = getattr(win, 'file_widget', None)
        if fw and hasattr(fw, 'dest_input'):
            fw.dest_input.setText(hash_str)

    def _copied(self):
        sb = self._find_status_bar()
        if sb:
            sb.showMessage("Hash copied to clipboard", 3000)

    def _find_status_bar(self):
        p = self.parent()
        while p:
            if hasattr(p, 'statusBar'):
                return p.statusBar()
            p = p.parent()
        return None

    def _announce_myself(self):
        if self.backend and hasattr(self.backend, 'announce_now'):
            self.backend.announce_now()
        sb = self._find_status_bar()
        if sb:
            sb.showMessage("Announced on network", 3000)
