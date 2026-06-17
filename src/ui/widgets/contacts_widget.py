"""Contacts tab placeholder."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton, QHBoxLayout, QInputDialog, QMessageBox


class ContactsWidget(QWidget):
    """Basic contacts list."""
    
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.contacts = []  # list of (name, hash)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("Contacts")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)
        
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Contact")
        add_btn.clicked.connect(self._add_contact)
        btn_layout.addWidget(add_btn)
        layout.addLayout(btn_layout)
        
        info = QLabel("Add known identity hashes here for easy sending.")
        info.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(info)
    
    def _add_contact(self):
        name, ok = QInputDialog.getText(self, "Add Contact", "Contact name:")
        if not ok or not name:
            return
        hash_str, ok = QInputDialog.getText(self, "Add Contact", "Identity hash:")
        if ok and hash_str:
            self.contacts.append((name, hash_str))
            self.list_widget.addItem(f"{name} - {hash_str[:12]}...")
            QMessageBox.information(self, "Added", f"Contact '{name}' added.")
