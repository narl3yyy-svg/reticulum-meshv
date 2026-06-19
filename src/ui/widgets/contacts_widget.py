"""Contacts widget showing discovered peers from the mesh."""

import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QScrollArea, QFrame, QGridLayout, QMenu,
    QApplication, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer
from src.config.theme import MeshTheme
from src.ui.widgets.common import EmptyState


class ContactCard(QFrame):
    def __init__(self, contact_data, parent=None):
        super().__init__(parent)
        self.contact_data = contact_data
        self.setFixedSize(220, 240)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
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
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name = contact_data.get('display_name', contact_data.get('hash', '')[:8])
        is_trusted = contact_data.get('is_trusted', False)

        avatar_frame = QFrame()
        avatar_frame.setFixedSize(64, 64)
        avatar_layout = QVBoxLayout(avatar_frame)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        avatar_label = QLabel(name[0].upper() if name else '?')
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_label.setStyleSheet(f"""
            background-color: {MeshTheme.ACCENT}30;
            color: {MeshTheme.ACCENT};
            font-size: 28px; font-weight: 700; border-radius: 32px;
        """)
        avatar_layout.addWidget(avatar_label)
        layout.addWidget(avatar_frame, 0, Qt.AlignmentFlag.AlignCenter)

        name_row = QHBoxLayout()
        name_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_row.setSpacing(4)
        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {MeshTheme.TEXT}; background: transparent;")
        name_row.addWidget(name_label)
        if is_trusted:
            badge = QLabel("\u2713")
            badge.setStyleSheet(f"font-size: 14px; color: {MeshTheme.SUCCESS}; background: transparent; font-weight: 700;")
            name_row.addWidget(badge)
        layout.addLayout(name_row)

        hash_str = contact_data.get('hash', '')[:12]
        hash_label = QLabel(hash_str)
        hash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hash_label.setStyleSheet(
            "font-family: 'JetBrains Mono', monospace; font-size: 10px; "
            f"color: {MeshTheme.TEXT_DIM}; background: transparent;")
        layout.addWidget(hash_label)

        status = contact_data.get('status', 'offline')
        sc = {'online': MeshTheme.SUCCESS, 'away': MeshTheme.WARNING, 'offline': MeshTheme.TEXT_DIM}
        status_label = QLabel(f"\u25CF {status.capitalize()}")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet(f"font-size: 11px; color: {sc.get(status, MeshTheme.TEXT_DIM)}; background: transparent;")
        layout.addWidget(status_label)

        btn = QPushButton("Message")
        btn.setFixedHeight(32)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MeshTheme.ACCENT}; color: white;
                border: none; border-radius: 8px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {MeshTheme.ACCENT_DARK}; }}
        """)
        btn.clicked.connect(self._message)
        layout.addWidget(btn)

    def _message(self):
        win = self.window()
        if hasattr(win, '_switch_to'):
            win._switch_to(0)
        mw = getattr(win, 'messages_widget', None)
        if mw is not None:
            h = self.contact_data.get('hash', '')
            n = self.contact_data.get('display_name', h[:8])
            mw.add_conversation(h, n)

    def _toggle_trust(self):
        h = self.contact_data.get('hash', '')
        win = self.window()
        if win and hasattr(win, 'backend') and win.backend and win.backend.contact_manager:
            mgr = win.backend.contact_manager
            c = mgr.get(h)
            if c:
                new_val = not c.is_trusted
                mgr.set_trusted(h, new_val)
                self.contact_data['is_trusted'] = new_val
                sb = self._sb()
                if sb:
                    sb.showMessage(f"{'Trusted' if new_val else 'Untrusted'} {self.contact_data.get('display_name', h[:8])}", 3000)

    def _sb(self):
        p = self.parent()
        while p:
            if hasattr(p, 'statusBar'):
                return p.statusBar()
            p = p.parent()
        return None

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background-color: {MeshTheme.SURFACE};
                border: 1px solid {MeshTheme.BORDER}; border-radius: 8px; padding: 4px; }}
            QMenu::item {{ padding: 6px 20px; border-radius: 4px; color: {MeshTheme.TEXT}; }}
            QMenu::item:selected {{ background-color: {MeshTheme.ACCENT}; color: white; }}
        """)
        h = self.contact_data.get('hash', '')
        is_trusted = self.contact_data.get('is_trusted', False)
        trust_label = "✓ Trusted" if is_trusted else "Trust"
        trust_a = menu.addAction(trust_label)
        copy_a = menu.addAction("Copy Identity Hash")
        delete_a = menu.addAction("Delete Contact")
        action = menu.exec(event.globalPos())
        if action == trust_a:
            self._toggle_trust()
        elif action == copy_a:
            QApplication.clipboard().setText(h)
        elif action == delete_a:
            parent_widget = self.parentWidget()
            while parent_widget and not hasattr(parent_widget, 'cards'):
                parent_widget = parent_widget.parentWidget()
            if parent_widget and hasattr(parent_widget, 'cards'):
                if self in parent_widget.cards:
                    parent_widget.cards.remove(self)
            self.setParent(None)
            self.deleteLater()


class ContactsWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QWidget()
        hdr = QHBoxLayout(header)
        hdr.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Contacts")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {MeshTheme.TEXT};")
        hdr.addWidget(title)

        self.announce_btn = QPushButton("Announce Myself")
        self.announce_btn.setFixedHeight(36)
        self.announce_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MeshTheme.ACCENT}; color: white;
                border: none; border-radius: 8px; padding: 6px 18px;
                font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {MeshTheme.ACCENT_DARK}; }}
        """)
        self.announce_btn.clicked.connect(self._announce)
        hdr.addStretch()
        hdr.addWidget(self.announce_btn)

        search = QLineEdit()
        search.setPlaceholderText("Search contacts...")
        search.setFixedWidth(200)
        search.setFixedHeight(36)
        search.setStyleSheet(f"""
            QLineEdit {{
                background-color: {MeshTheme.INPUT_BG}; color: {MeshTheme.TEXT};
                border: 1px solid {MeshTheme.INPUT_BORDER}; border-radius: 8px;
                padding: 6px 12px; font-size: 13px;
            }}
            QLineEdit:focus {{ border: 2px solid {MeshTheme.ACCENT}; }}
        """)
        search.textChanged.connect(self._filter_cards)
        hdr.addWidget(search)

        add_btn = QPushButton("+ Add")
        add_btn.setFixedHeight(36)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; color: {MeshTheme.ACCENT};
                border: 1px solid {MeshTheme.ACCENT}; border-radius: 8px;
                padding: 6px 14px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {MeshTheme.ACCENT}20; }}
        """)
        add_btn.clicked.connect(self._add_contact)
        hdr.addWidget(add_btn)
        layout.addWidget(header)

        self.contacts_empty = EmptyState("\U0001F465", "No contacts yet", "Contacts appear here when discovered on the mesh or added manually")
        layout.addWidget(self.contacts_empty)

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

        self.cards = []
        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh)
        self._timer.start(10000)
        self._refresh()

    def _refresh(self):
        self._clear_grid()
        peers = []
        seen = set()
        if self.backend.network_monitor:
            peers = self.backend.network_monitor.get_peers()
            for p in peers:
                h = p.get("hash", "")
                if h in seen:
                    continue
                seen.add(h)
                age = time.time() - p.get("last_seen", 0)
                status = "online" if age < 300 else "away" if age < 3600 else "offline"
                is_trusted = False
                if self.backend.contact_manager:
                    is_trusted = self.backend.contact_manager.check_trusted(h)
                self.add_contact({
                    "hash": h,
                    "display_name": p.get("app_data", h[:8]),
                    "status": status,
                    "is_trusted": is_trusted,
                })
        if self.backend.contact_manager:
            for c in self.backend.contact_manager.get_all():
                if c.hash_hex not in seen:
                    seen.add(c.hash_hex)
                    age = time.time() - c.last_seen
                    status = "online" if age < 300 else "offline"
                    self.add_contact({
                        "hash": c.hash_hex,
                        "display_name": c.name,
                        "status": status,
                        "is_trusted": c.is_trusted,
                    })
        if not self.cards and self.backend.rns_node:
            self.add_contact({
                "hash": self.backend.rns_node.get_identity_hash(),
                "display_name": "You",
                "status": "online",
            })
        self.contacts_empty.setVisible(len(self.cards) == 0)

    def _clear_grid(self):
        for card in self.cards[:]:
            try:
                self.grid.removeWidget(card)
                card.setParent(None)
                card.deleteLater()
            except RuntimeError:
                pass
        self.cards = []

    def add_contact(self, data):
        card = ContactCard(data)
        self.cards.append(card)
        idx = len(self.cards) - 1
        self.grid.addWidget(card, idx // 4, idx % 4)
        self.contacts_empty.setVisible(False)

    def _announce(self):
        if self.backend:
            self.backend.announce_now()

    def _add_contact(self):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Add Contact")
        dialog.setLabelText("Enter identity hash:")
        if dialog.exec():
            h = dialog.textValue().strip()
            if h:
                self.add_contact({"hash": h, "display_name": h[:16], "status": "offline"})

    def _filter_cards(self, text):
        for card in self.cards:
            n = card.contact_data.get('display_name', '')
            h = card.contact_data.get('hash', '')
            card.setVisible(text.lower() in n.lower() or text.lower() in h.lower())

    def _cleanup(self):
        if self._timer and self._timer.isActive():
            self._timer.stop()
