"""Enhanced Contacts widget with persistent storage and discovery."""

import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QInputDialog,
    QMessageBox, QGroupBox, QMenu, QApplication
)
from PyQt6.QtCore import Qt, QTimer


class ContactsWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.rns_node = backend.rns_node
        self.contact_mgr = backend.contact_manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Contacts")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        announce_group = QGroupBox("Network Presence")
        announce_layout = QVBoxLayout()

        announce_btn = QPushButton("Announce Myself on Network")
        announce_btn.setStyleSheet("font-weight: bold;")
        announce_btn.clicked.connect(self._announce)
        announce_layout.addWidget(announce_btn)

        announce_info = QLabel("Makes you visible to other nodes via LXMF and Reticulum")
        announce_info.setStyleSheet("color: #888; font-size: 11px;")
        announce_layout.addWidget(announce_info)

        announce_group.setLayout(announce_layout)
        layout.addWidget(announce_group)

        search_group = QGroupBox("Search Contacts")
        search_layout = QVBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search by name or hash...")
        self.search_input.textChanged.connect(self._refresh_lists)
        search_layout.addWidget(self.search_input)
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

        disc_group = QGroupBox("Discovered Peers")
        disc_layout = QVBoxLayout()

        self.discovered_list = QListWidget()
        self.discovered_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.discovered_list.customContextMenuRequested.connect(self._show_discovered_menu)
        disc_layout.addWidget(self.discovered_list)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_lists)
        disc_layout.addWidget(refresh_btn)

        disc_group.setLayout(disc_layout)
        layout.addWidget(disc_group)

        my_group = QGroupBox("My Contacts")
        my_layout = QVBoxLayout()

        self.contacts_list = QListWidget()
        self.contacts_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.contacts_list.customContextMenuRequested.connect(self._show_contacts_menu)
        my_layout.addWidget(self.contacts_list)

        add_btn = QPushButton("Add Contact Manually")
        add_btn.clicked.connect(self._add_contact)
        my_layout.addWidget(add_btn)

        my_group.setLayout(my_layout)
        layout.addWidget(my_group)

        self.timer = QTimer()
        self.timer.timeout.connect(self._refresh_lists)
        self.timer.start(15000)

        self._refresh_lists()

    def _announce(self):
        announced = False
        if self.backend.lxmf_messenger:
            announced = self.backend.lxmf_messenger.announce()
        if not announced and self.rns_node:
            announced = self.rns_node.announce_myself()

        if announced:
            QMessageBox.information(self, "Announced", "You are now visible on the network.")
        else:
            QMessageBox.warning(self, "Error", "Could not announce")

    def _refresh_lists(self):
        query = self.search_input.text().strip().lower()

        self.discovered_list.clear()
        peers = self.rns_node.get_discovered_peers() if self.rns_node else []
        for h, info in peers:
            if query and query not in h[:12]:
                continue
            display = f"{info.get('name', h[:12])} — {int(time.time() - info.get('last_seen', 0))}s ago"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, h)
            self.discovered_list.addItem(item)

        self.contacts_list.clear()
        contacts = self.contact_mgr.get_all() if self.contact_mgr else []
        for c in contacts:
            if query and query not in c.name.lower() and query not in c.hash_hex.lower():
                continue
            display = f"{c.name} — {c.hash_hex[:12]}..."
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, c.hash_hex)
            item.setData(Qt.ItemDataRole.ToolTipRole, f"Hash: {c.hash_hex}\nLast seen: {c.last_seen}")
            self.contacts_list.addItem(item)

    def _show_discovered_menu(self, pos):
        item = self.discovered_list.itemAt(pos)
        if not item:
            return
        hash_hex = item.data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)
        add_action = menu.addAction("Add to My Contacts")
        add_action.triggered.connect(lambda: self._add_discovered(hash_hex))

        copy_action = menu.addAction("Copy Hash")
        copy_action.triggered.connect(lambda: self._copy_hash(hash_hex))

        menu.exec(self.discovered_list.viewport().mapToGlobal(pos))

    def _add_discovered(self, hash_hex):
        name, ok = QInputDialog.getText(self, "Add Contact", "Name:", text=hash_hex[:12])
        if ok and name:
            self.contact_mgr.add_or_update(hash_hex, name=name)
            self._refresh_lists()
            QMessageBox.information(self, "Added", f"Added {name}")

    def _copy_hash(self, h):
        QApplication.clipboard().setText(h)

    def _add_contact(self):
        name, ok = QInputDialog.getText(self, "Add Contact", "Contact name:")
        if not ok or not name:
            return
        hash_str, ok = QInputDialog.getText(self, "Add Contact", "Identity hash (64 hex chars):")
        if ok and hash_str:
            hash_str = hash_str.strip().lower()
            if len(hash_str) == 64:
                self.contact_mgr.add_or_update(hash_str, name=name)
                self._refresh_lists()
            else:
                QMessageBox.warning(self, "Invalid", "Hash must be 64 hex characters.")

    def _show_contacts_menu(self, pos):
        item = self.contacts_list.itemAt(pos)
        if not item:
            return
        hash_hex = item.data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)
        copy_action = menu.addAction("Copy Hash")
        copy_action.triggered.connect(lambda: self._copy_hash(hash_hex))

        chat_action = menu.addAction("Start Chat")
        chat_action.triggered.connect(lambda: self._start_chat_with(hash_hex))

        rename_action = menu.addAction("Rename")
        rename_action.triggered.connect(lambda: self._rename_contact(hash_hex))

        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self._delete_contact(hash_hex))

        menu.exec(self.contacts_list.viewport().mapToGlobal(pos))

    def _start_chat_with(self, hash_hex):
        mw = self.backend.main_window
        if mw:
            mw.dest_input.setText(hash_hex)
            mw.stack.setCurrentIndex(0)

    def _rename_contact(self, hash_hex):
        c = self.contact_mgr.get(hash_hex)
        if not c:
            return
        name, ok = QInputDialog.getText(self, "Rename", "New name:", text=c.name)
        if ok and name:
            self.contact_mgr.add_or_update(hash_hex, name=name)
            self._refresh_lists()

    def _delete_contact(self, hash_hex):
        c = self.contact_mgr.get(hash_hex)
        if c:
            reply = QMessageBox.question(self, "Delete", f"Delete {c.name}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.contact_mgr.remove(hash_hex)
                self._refresh_lists()
