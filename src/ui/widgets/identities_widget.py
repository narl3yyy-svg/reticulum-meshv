"""Multi-identity management widget."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QInputDialog, QMessageBox,
    QGroupBox, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt


class IdentitiesWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.identity_mgr = backend.identity_manager
        self.rns_node = backend.rns_node

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Identity Manager")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        current_group = QGroupBox("Current Identity")
        current_layout = QVBoxLayout()

        current_hash = self.rns_node.get_identity_hash() if self.rns_node else "N/A"
        self.current_label = QLabel(current_hash)
        self.current_label.setStyleSheet("font-family: monospace; background: #2a2a2a; padding: 10px; border-radius: 6px;")
        self.current_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        current_layout.addWidget(self.current_label)

        copy_btn = QPushButton("Copy Hash")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(current_hash))
        current_layout.addWidget(copy_btn)

        current_group.setLayout(current_layout)
        layout.addWidget(current_group)

        manage_group = QGroupBox("Saved Identities")
        manage_layout = QVBoxLayout()

        self.identity_list = QListWidget()
        self.identity_list.itemDoubleClicked.connect(self._switch_identity)
        manage_layout.addWidget(self.identity_list)

        btn_row = QHBoxLayout()
        create_btn = QPushButton("Create New")
        create_btn.clicked.connect(self._create_identity)
        btn_row.addWidget(create_btn)

        import_btn = QPushButton("Import from File")
        import_btn.clicked.connect(self._import_identity)
        btn_row.addWidget(import_btn)

        switch_btn = QPushButton("Switch to Selected")
        switch_btn.clicked.connect(self._switch_identity)
        btn_row.addWidget(switch_btn)

        delete_btn = QPushButton("Delete Selected")
        delete_btn.setStyleSheet("background-color: #d32f2f;")
        delete_btn.clicked.connect(self._delete_identity)
        btn_row.addWidget(delete_btn)

        manage_layout.addLayout(btn_row)
        manage_group.setLayout(manage_layout)
        layout.addWidget(manage_group)

        note = QLabel("Note: Switching identities requires app restart to take full effect.")
        note.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(note)

        layout.addStretch()

        self._refresh_list()

    def _refresh_list(self):
        self.identity_list.clear()
        identities = self.identity_mgr.list_identities() if self.identity_mgr else []
        current_hash = self.rns_node.get_identity_hash() if self.rns_node else ""

        for info in identities:
            h = info["hash"]
            name = info.get("name", h[:12])
            is_active = h == current_hash
            prefix = "● " if is_active else "  "
            display = f"{prefix}{name} — {h[:12]}..."
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, h)
            if is_active:
                item.setForeground(Qt.GlobalColor.green)
            self.identity_list.addItem(item)

    def _create_identity(self):
        name, ok = QInputDialog.getText(self, "New Identity", "Name (optional):")
        if ok:
            self.identity_mgr.create_identity(name=name.strip())
            self._refresh_list()
            QMessageBox.information(self, "Created", "New identity created. Switch to it and restart to use.")

    def _import_identity(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Identity Key", "", "Key files (*.key);;All files (*)")
        if path:
            identity = self.identity_mgr.import_identity(path)
            if identity:
                self._refresh_list()
                QMessageBox.information(self, "Imported", "Identity imported successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to import identity key.")

    def _switch_identity(self):
        item = self.identity_list.currentItem()
        if not item:
            return
        hash_hex = item.data(Qt.ItemDataRole.UserRole)
        identity = self.identity_mgr.load_identity(hash_hex)
        if identity:
            self.identity_mgr.set_active(hash_hex)
            reply = QMessageBox.question(
                self, "Switch Identity",
                "Identity selected. Restart the application to apply?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                import os, sys
                os.execv(sys.executable, [sys.executable, "-m", "src.main"])
        else:
            QMessageBox.warning(self, "Error", "Could not load identity.")

    def _delete_identity(self):
        item = self.identity_list.currentItem()
        if not item:
            return
        hash_hex = item.data(Qt.ItemDataRole.UserRole)
        current_hash = self.rns_node.get_identity_hash() if self.rns_node else ""
        if hash_hex == current_hash:
            QMessageBox.warning(self, "Error", "Cannot delete the currently active identity.")
            return
        reply = QMessageBox.question(self, "Delete", "Delete this identity permanently?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.identity_mgr.delete_identity(hash_hex)
            self._refresh_list()
