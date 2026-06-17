"""Contacts tab with add, delete, and copy hash."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton, 
    QHBoxLayout, QInputDialog, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication


class ContactsWidget(QWidget):
    """Contacts list with management features."""
    
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
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.list_widget)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Contact")
        add_btn.clicked.connect(self._add_contact)
        btn_layout.addWidget(add_btn)
        layout.addLayout(btn_layout)
        
        info = QLabel("Right-click a contact to copy hash or delete.")
        info.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(info)
    
    def _add_contact(self):
        name, ok = QInputDialog.getText(self, "Add Contact", "Contact name:")
        if not ok or not name:
            return
        hash_str, ok = QInputDialog.getText(self, "Add Contact", "Identity / Destination hash:")
        if ok and hash_str:
            self.contacts.append((name.strip(), hash_str.strip()))
            self._refresh_list()
            QMessageBox.information(self, "Added", f"Contact '{name}' added.")
    
    def _refresh_list(self):
        self.list_widget.clear()
        for name, h in self.contacts:
            display = f"{name}  —  {h[:12]}...{h[-4:] if len(h) > 16 else h}"
            self.list_widget.addItem(display)
    
    def _show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        
        row = self.list_widget.row(item)
        if row < 0 or row >= len(self.contacts):
            return
        
        menu = QMenu(self)
        
        copy_action = QAction("Copy Hash", self)
        copy_action.triggered.connect(lambda: self._copy_hash(row))
        menu.addAction(copy_action)
        
        delete_action = QAction("Delete Contact", self)
        delete_action.triggered.connect(lambda: self._delete_contact(row))
        menu.addAction(delete_action)
        
        menu.exec(self.list_widget.viewport().mapToGlobal(pos))
    
    def _copy_hash(self, row):
        if 0 <= row < len(self.contacts):
            _, h = self.contacts[row]
            clipboard = QApplication.clipboard()
            clipboard.setText(h)
            QMessageBox.information(self, "Copied", "Hash copied to clipboard!")
    
    def _delete_contact(self, row):
        if 0 <= row < len(self.contacts):
            name, _ = self.contacts.pop(row)
            self._refresh_list()
            QMessageBox.information(self, "Deleted", f"Contact '{name}' removed.")
