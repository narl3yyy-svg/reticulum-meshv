"""Main application window."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QLabel, QStatusBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from src.config.theme import get_stylesheet
from src.ui.widgets.file_manager_widget import FileManagerWidget

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.setWindowTitle("Reticulum Mesh")
        self.setGeometry(100, 100, 1200, 820)
        self.setStyleSheet(get_stylesheet())
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setMaximumWidth(220)
        self.sidebar.itemClicked.connect(self._on_nav)
        
        items = ["💬 Messages", "📁 Files", "👥 Contacts", "⚙️ Settings"]
        for idx, text in enumerate(items):
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self.sidebar.addItem(item)
        
        layout.addWidget(self.sidebar, 0)
        
        # Content stack
        self.stack = QStackedWidget()
        self.file_widget = FileManagerWidget(backend)
        self.stack.addWidget(QWidget())  # Messages placeholder
        self.stack.addWidget(self.file_widget)
        self.stack.addWidget(QWidget())  # Contacts placeholder
        self.stack.addWidget(QWidget())  # Settings placeholder
        
        layout.addWidget(self.stack, 1)
        
        # Status bar
        status_text = f"Identity: {backend.rns_node.get_identity_hash()[:12]}... | Status: Ready"
        self.statusBar().addWidget(QLabel(status_text))
        
        self.show()
    
    def _on_nav(self, item):
        """Handle navigation."""
        index = item.data(Qt.ItemDataRole.UserRole)
        self.stack.setCurrentIndex(index)
