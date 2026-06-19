"""Main application window with all feature tabs."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QLabel, QPushButton
)
from PyQt6.QtCore import Qt
from src.config.theme import get_stylesheet
from src.ui.widgets.file_manager_widget import FileManagerWidget
from src.ui.widgets.settings_widget import SettingsWidget
from src.ui.widgets.messages_widget import MessagesWidget
from src.ui.widgets.contacts_widget import ContactsWidget
from src.ui.widgets.interfaces_widget import InterfacesWidget
from src.ui.widgets.identities_widget import IdentitiesWidget
from src.ui.widgets.network_widget import NetworkWidget
from src.ui.widgets.telephony_widget import TelephonyWidget


class MainWindow(QMainWindow):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.setWindowTitle("Reticulum Mesh – Mesh Networking Suite")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet(get_stylesheet())

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setMaximumWidth(220)
        self.sidebar.itemClicked.connect(self._on_nav)

        items = [
            ("💬 Messages", 0),
            ("📁 Files", 1),
            ("👥 Contacts", 2),
            ("🆔 Identities", 3),
            ("🌐 Network", 4),
            ("📞 Telephony", 5),
            ("🔌 Interfaces", 6),
            ("⚙️ Settings", 7),
        ]
        for text, idx in items:
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self.sidebar.addItem(item)

        layout.addWidget(self.sidebar, 0)

        self.stack = QStackedWidget()

        self.messages_widget = MessagesWidget(backend)
        self.file_widget = FileManagerWidget(backend)
        self.contacts_widget = ContactsWidget(backend)
        self.identities_widget = IdentitiesWidget(backend)
        self.network_widget = NetworkWidget(backend)
        self.telephony_widget = TelephonyWidget(backend)
        self.interfaces_widget = InterfacesWidget(backend)
        self.settings_widget = SettingsWidget(backend)

        self.stack.addWidget(self.messages_widget)    # 0
        self.stack.addWidget(self.file_widget)         # 1
        self.stack.addWidget(self.contacts_widget)     # 2
        self.stack.addWidget(self.identities_widget)   # 3
        self.stack.addWidget(self.network_widget)      # 4
        self.stack.addWidget(self.telephony_widget)    # 5
        self.stack.addWidget(self.interfaces_widget)   # 6
        self.stack.addWidget(self.settings_widget)     # 7

        layout.addWidget(self.stack, 1)

        identity_text = backend.rns_node.get_short_identity_hash() if backend.rns_node else "N/A"
        self.identity_status = QLabel(f"Identity: {identity_text}")
        self.identity_status.setStyleSheet("font-family: monospace;")

        copy_btn = QPushButton("📋")
        copy_btn.setMaximumWidth(28)
        copy_btn.setToolTip("Copy your identity hash")
        copy_btn.clicked.connect(self._copy_identity)

        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(8, 2, 8, 2)
        status_layout.addWidget(self.identity_status)
        status_layout.addWidget(copy_btn)
        status_layout.addStretch()

        self.statusBar().addWidget(status_widget, 1)

        self.show()

    def _copy_identity(self):
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        if self.backend.rns_node:
            clipboard.setText(self.backend.rns_node.get_identity_hash())
        self.statusBar().showMessage("Identity hash copied!", 3000)

    def _on_nav(self, item):
        index = item.data(Qt.ItemDataRole.UserRole)
        self.stack.setCurrentIndex(index)
