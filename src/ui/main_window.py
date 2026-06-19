"""MeshChatX-inspired main window with sidebar navigation."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QFrame,
    QListWidget, QScrollArea
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
from src.config.theme import get_stylesheet, MeshTheme


class NavButton(QPushButton):
    def __init__(self, text, icon_char, index):
        super().__init__(f"  {icon_char}  {text}")
        self.nav_index = index
        self.setCheckable(True)
        self.setFixedHeight(42)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {MeshTheme.TEXT_MUTED};
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                text-align: left;
                font-size: 14px;
                font-weight: 400;
            }}
            QPushButton:hover {{
                background-color: {MeshTheme.SIDEBAR_HOVER};
                color: {MeshTheme.TEXT};
            }}
            QPushButton:checked {{
                background-color: {MeshTheme.ACCENT}20;
                color: {MeshTheme.ACCENT};
                font-weight: 600;
            }}
        """)

    def set_active(self, active: bool):
        self.setChecked(active)


class MainWindow(QMainWindow):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.setWindowTitle("RMESHV – Reticulum Mesh")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet(get_stylesheet())

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = self._build_sidebar()
        layout.addWidget(self.sidebar, 0)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

        self._init_widgets(backend)
        self.nav_buttons[0].set_active(True)

        self._build_statusbar()
        self.show()

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {MeshTheme.SIDEBAR_BG};
                border-right: 1px solid {MeshTheme.BORDER};
            }}
        """)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(2)

        logo = QLabel("  RMESHV")
        logo.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {MeshTheme.ACCENT};
            padding: 8px 12px 16px 12px;
            letter-spacing: 2px;
        """)
        layout.addWidget(logo)

        self.nav_buttons = []

        self.nav_items = [
            ("Messages", "\U0001F4AC", 0),
            ("Files", "\U0001F4C1", 1),
            ("Contacts", "\U0001F465", 2),
            ("Announces", "\U0001F4E2", 3),
            ("Identities", "\U0001F464", 4),
            ("Network", "\U0001F310", 5),
            ("Telephony", "\U0001F4DE", 6),
            ("Interfaces", "\U0001F50C", 7),
            ("Settings", "\u2699\uFE0F", 8),
        ]

        for text, icon, idx in self.nav_items:
            btn = NavButton(text, icon, idx)
            btn.clicked.connect(lambda checked, i=idx: self._switch_to(i))
            self.nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        identity_frame = QFrame()
        identity_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {MeshTheme.SURFACE};
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        id_layout = QVBoxLayout(identity_frame)
        id_layout.setContentsMargins(12, 12, 12, 12)
        id_layout.setSpacing(6)

        id_header = QLabel("My Identity")
        id_header.setStyleSheet(f"font-size: 11px; color: {MeshTheme.TEXT_DIM}; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; background: transparent;")
        id_layout.addWidget(id_header)

        from PyQt6.QtWidgets import QLineEdit
        display_name = self.backend.get_display_name()
        self.sidebar_name = QLineEdit(display_name)
        self.sidebar_name.setStyleSheet(f"""
            QLineEdit {{
                background-color: {MeshTheme.INPUT_BG};
                color: {MeshTheme.TEXT};
                border: 1px solid {MeshTheme.INPUT_BORDER};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
                font-weight: 600;
            }}
            QLineEdit:focus {{ border: 2px solid {MeshTheme.ACCENT}; }}
        """)
        self.sidebar_name.setPlaceholderText("Your display name")
        self.sidebar_name.textChanged.connect(self._on_name_changed)
        id_layout.addWidget(self.sidebar_name)

        hash_text = self.backend.rns_node.get_short_identity_hash() if self.backend.rns_node else "N/A"
        self.sidebar_hash = QLabel(hash_text)
        self.sidebar_hash.setStyleSheet(f"font-family: 'JetBrains Mono', monospace; font-size: 11px; color: {MeshTheme.TEXT_MUTED}; background: transparent;")
        self.sidebar_hash.setWordWrap(True)
        id_layout.addWidget(self.sidebar_hash)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        announce_btn = QPushButton("Announce")
        announce_btn.setFixedHeight(28)
        announce_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MeshTheme.ACCENT};
                color: white; border: none; border-radius: 6px;
                padding: 4px 12px; font-size: 11px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {MeshTheme.ACCENT_DARK}; }}
        """)
        announce_btn.clicked.connect(self._sidebar_announce)
        btn_row.addWidget(announce_btn)

        copy_btn = QPushButton("Copy")
        copy_btn.setFixedHeight(28)
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {MeshTheme.TEXT_MUTED}; border: 1px solid {MeshTheme.BORDER};
                border-radius: 6px; padding: 4px 12px; font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {MeshTheme.SURFACE_VARIANT}; color: {MeshTheme.TEXT};
            }}
        """)
        copy_btn.clicked.connect(self._copy_identity)
        btn_row.addWidget(copy_btn)

        id_layout.addLayout(btn_row)
        layout.addWidget(identity_frame)

        return sidebar

    def _build_statusbar(self):
        identity_text = self.backend.rns_node.get_short_identity_hash() if self.backend.rns_node else "N/A"
        self.status_label = QLabel(f"Identity: {identity_text}")
        self.status_label.setStyleSheet(f"font-family: 'JetBrains Mono', monospace; font-size: 11px; color: {MeshTheme.TEXT_DIM}; padding: 2px 8px;")
        self.statusBar().addWidget(self.status_label, 1)

    def _switch_to(self, index):
        for i, btn in enumerate(self.nav_buttons):
            btn.set_active(i == index)
        self.stack.setCurrentIndex(index)

    def _on_name_changed(self, text):
        self.backend.set_display_name(text)
        self.statusBar().showMessage("Display name updated", 2000)

    def _sidebar_announce(self):
        self.backend.announce_now()
        self.statusBar().showMessage("Announced on network", 3000)

    def _copy_identity(self):
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        if self.backend.rns_node:
            clipboard.setText(self.backend.rns_node.get_identity_hash())
        self.statusBar().showMessage("Identity hash copied!", 3000)

    def _init_widgets(self, backend):
        from src.ui.widgets.file_manager_widget import FileManagerWidget
        from src.ui.widgets.settings_widget import SettingsWidget
        from src.ui.widgets.messages_widget import MessagesWidget
        from src.ui.widgets.contacts_widget import ContactsWidget
        from src.ui.widgets.announces_widget import AnnouncesWidget
        from src.ui.widgets.interfaces_widget import InterfacesWidget
        from src.ui.widgets.identities_widget import IdentitiesWidget
        from src.ui.widgets.network_widget import NetworkWidget
        from src.ui.widgets.telephony_widget import TelephonyWidget

        self.messages_widget = MessagesWidget(backend)
        self.file_widget = FileManagerWidget(backend)
        self.contacts_widget = ContactsWidget(backend)
        self.announces_widget = AnnouncesWidget(backend)
        self.identities_widget = IdentitiesWidget(backend)
        self.network_widget = NetworkWidget(backend)
        self.telephony_widget = TelephonyWidget(backend)
        self.interfaces_widget = InterfacesWidget(backend)
        self.settings_widget = SettingsWidget(backend)

        self.stack.addWidget(self.messages_widget)
        self.stack.addWidget(self.file_widget)
        self.stack.addWidget(self.contacts_widget)
        self.stack.addWidget(self.announces_widget)
        self.stack.addWidget(self.identities_widget)
        self.stack.addWidget(self.network_widget)
        self.stack.addWidget(self.telephony_widget)
        self.stack.addWidget(self.interfaces_widget)
        self.stack.addWidget(self.settings_widget)
