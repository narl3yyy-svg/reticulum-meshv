"""Main application window."""

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


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.setWindowTitle("Reticulum Mesh – Easy Mesh File Sharing")
        self.setGeometry(100, 100, 1200, 820)
        self.setStyleSheet(get_stylesheet())
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.sidebar = QListWidget()
        self.sidebar.setMaximumWidth(220)
        self.sidebar.itemClicked.connect(self._on_nav)
        
        items = ["💬 Messages", "📁 Files", "👥 Contacts", "⚙️ Settings"]
        for idx, text in enumerate(items):
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self.sidebar.addItem(item)
        
        layout.addWidget(self.sidebar, 0)
        
        self.stack = QStackedWidget()
        self.messages_widget = MessagesWidget(backend)
        self.file_widget = FileManagerWidget(backend)
        self.contacts_widget = ContactsWidget(backend)
        self.settings_widget = SettingsWidget(backend)
        
        self.stack.addWidget(self.messages_widget)
        self.stack.addWidget(self.file_widget)
        self.stack.addWidget(self.contacts_widget)
        self.stack.addWidget(self.settings_widget)
        
        layout.addWidget(self.stack, 1)
        
        # Status bar
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(8, 2, 8, 2)
        
        identity_text = backend.rns_node.get_short_identity_hash()
        self.identity_status = QLabel(f"Identity: {identity_text}")
        self.identity_status.setStyleSheet("font-family: monospace;")
        
        copy_status_btn = QPushButton("📋")
        copy_status_btn.setMaximumWidth(28)
        copy_status_btn.setToolTip("Copy your identity hash")
        copy_status_btn.clicked.connect(self._copy_identity_from_status)
        
        status_layout.addWidget(self.identity_status)
        status_layout.addWidget(copy_status_btn)
        status_layout.addStretch()
        
        self.statusBar().addWidget(status_widget, 1)
        
        self.show()
    
    def _copy_identity_from_status(self):
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.backend.rns_node.get_identity_hash())
        self.statusBar().showMessage("Identity hash copied!", 3000)
    
    def _on_nav(self, item):
        index = item.data(Qt.ItemDataRole.UserRole)
        self.stack.setCurrentIndex(index)
