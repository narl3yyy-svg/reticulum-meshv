"""MeshChatX-inspired contacts widget with card layout."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QScrollArea, QFrame, QGridLayout, QSizePolicy,
    QMenu, QApplication
)
from PyQt6.QtCore import Qt, QSize, QDateTime
from PyQt6.QtGui import QFont, QPainter, QColor, QBrush, QPen
import time
from src.config.theme import MeshTheme


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
        label = QLabel(name[0].upper() if name else '?')
        label.setFixedSize(64, 64)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"""
            background-color: {MeshTheme.ACCENT}30;
            color: {MeshTheme.ACCENT};
            font-size: 28px;
            font-weight: 700;
            border-radius: 32px;
        """)
        layout.addWidget(label, 0, Qt.AlignmentFlag.AlignCenter)

        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {MeshTheme.TEXT}; background: transparent;")
        font = name_label.font()
        metrics = name_label.fontMetrics()
        elided = metrics.elidedText(name, Qt.TextElideMode.ElideRight, 180)
        name_label.setText(elided)
        layout.addWidget(name_label)

        hash_str = contact_data.get('hash', '')[:12]
        hash_label = QLabel(hash_str)
        hash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hash_label.setStyleSheet(f"font-family: 'JetBrains Mono', monospace; font-size: 10px; color: {MeshTheme.TEXT_DIM}; background: transparent;")
        layout.addWidget(hash_label)

        status = contact_data.get('status', 'offline')
        status_colors = {'online': MeshTheme.SUCCESS, 'away': MeshTheme.WARNING, 'offline': MeshTheme.TEXT_DIM}
        color = status_colors.get(status, MeshTheme.TEXT_DIM)
        status_label = QLabel(f"\u25CF {status.capitalize()}")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet(f"font-size: 11px; color: {color}; background: transparent;")
        layout.addWidget(status_label)

        btn = QPushButton("Message")
        btn.setFixedHeight(32)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MeshTheme.ACCENT};
                color: white; border: none; border-radius: 8px;
                font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {MeshTheme.ACCENT_DARK}; }}
        """)
        btn.clicked.connect(self._message)
        layout.addWidget(btn)

    def _message(self):
        from PyQt6.QtWidgets import QApplication
        win = self.window()
        if hasattr(win, '_switch_to'):
            win._switch_to(0)
        if hasattr(win, 'messages_widget'):
            hash_val = self.contact_data.get('hash', '')
            if isinstance(win.messages_widget, QWidget):
                from PyQt6.QtCore import QDateTime
                win.messages_widget.add_conversation(
                    hash_val,
                    self.contact_data.get('display_name', hash_val[:8])
                )

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {MeshTheme.SURFACE};
                border: 1px solid {MeshTheme.BORDER}; border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 20px; border-radius: 4px;
                color: {MeshTheme.TEXT};
            }}
            QMenu::item:selected {{
                background-color: {MeshTheme.ACCENT}; color: white;
            }}
        """)
        copy_action = menu.addAction("Copy Identity Hash")
        delete_action = menu.addAction("Delete Contact")
        action = menu.exec(event.globalPos())
        if action == copy_action:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.contact_data.get('hash', ''))
        elif action == delete_action:
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
        hdr_layout = QHBoxLayout(header)
        hdr_layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Contacts")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {MeshTheme.TEXT}; background: transparent;")
        hdr_layout.addWidget(title)

        search = QLineEdit()
        search.setPlaceholderText("\U0001F50D Search contacts...")
        search.setFixedWidth(240)
        search.setFixedHeight(36)
        search.setStyleSheet(f"""
            QLineEdit {{
                background-color: {MeshTheme.INPUT_BG};
                color: {MeshTheme.TEXT}; border: 1px solid {MeshTheme.INPUT_BORDER};
                border-radius: 8px; padding: 6px 12px; font-size: 13px;
            }}
            QLineEdit:focus {{ border: 2px solid {MeshTheme.ACCENT}; }}
            QLineEdit::placeholder {{ color: {MeshTheme.TEXT_DIM}; }}
        """)
        search.textChanged.connect(self._filter_cards)
        hdr_layout.addStretch()
        hdr_layout.addWidget(search)

        add_btn = QPushButton("+ Add Contact")
        add_btn.setFixedHeight(36)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MeshTheme.ACCENT};
                color: white; border: none; border-radius: 8px;
                padding: 6px 18px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {MeshTheme.ACCENT_DARK}; }}
        """)
        add_btn.clicked.connect(self._add_contact)
        hdr_layout.addWidget(add_btn)
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

        self.cards = []
        self._populate_contacts()

    def _populate_contacts(self):
        if self.backend.contact_manager:
            for contact in self.backend.contact_manager.get_all():
                data = {
                    'hash': contact.hash_hex,
                    'display_name': contact.name,
                    'status': 'online' if time.time() - contact.last_seen < 300 else 'offline',
                }
                self.add_contact(data)
        else:
            sample_data = [
                {'hash': 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6', 'display_name': 'Alice', 'status': 'online'},
                {'hash': 'b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1', 'display_name': 'Bob', 'status': 'away'},
                {'hash': 'c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1b2', 'display_name': 'Charlie (Relay)', 'status': 'online'},
                {'hash': 'd4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1b2c3', 'display_name': 'Diana', 'status': 'offline'},
                {'hash': 'e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1b2c3d4', 'display_name': 'Eve (Node)', 'status': 'online'},
            ]
            for data in sample_data:
                self.add_contact(data)

    def add_contact(self, data):
        card = ContactCard(data)
        self.cards.append(card)
        idx = len(self.cards) - 1
        row = idx // 4
        col = idx % 4
        self.grid.addWidget(card, row, col)

    def _add_contact(self):
        from PyQt6.QtWidgets import QInputDialog, QLineEdit
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Add Contact")
        dialog.setLabelText("Enter destination identity hash:")
        if dialog.exec():
            hash_val = dialog.textValue().strip()
            if hash_val:
                data = {'hash': hash_val, 'display_name': hash_val[:16], 'status': 'offline'}
                self.add_contact(data)

    def _filter_cards(self, text):
        for card in self.cards:
            name = card.contact_data.get('display_name', '')
            hash_val = card.contact_data.get('hash', '')
            visible = text.lower() in name.lower() or text.lower() in hash_val.lower()
            card.setVisible(visible)
