"""Contacts tab with Announce button and clearer peer discovery."""

import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton, 
    QHBoxLayout, QInputDialog, QMessageBox, QMenu, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication


class ContactsWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.rns_node = backend.rns_node
        self.contacts = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # === Announce Section (moved here from Interfaces) ===
        announce_group = QGroupBox("Network Presence")
        announce_layout = QVBoxLayout()

        announce_btn = QPushButton("Announce Myself on Network")
        announce_btn.setStyleSheet("font-weight: bold;")
        announce_btn.clicked.connect(self._announce_myself)
        announce_layout.addWidget(announce_btn)

        announce_info = QLabel("This makes you visible to other nodes so they can discover you.")
        announce_info.setStyleSheet("color: #888; font-size: 11px;")
        announce_layout.addWidget(announce_info)

        announce_group.setLayout(announce_layout)
        layout.addWidget(announce_group)

        # === Discovered Peers ===
        discovered_group = QGroupBox("Discovered Peers (from network announcements)")
        discovered_layout = QVBoxLayout()

        self.discovered_list = QListWidget()
        self.discovered_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.discovered_list.customContextMenuRequested.connect(self._show_discovered_menu)
        discovered_layout.addWidget(self.discovered_list)

        refresh_btn = QPushButton("Refresh Discovered Peers")
        refresh_btn.clicked.connect(self._refresh_discovered)
        discovered_layout.addWidget(refresh_btn)

        discovered_group.setLayout(discovered_layout)
        layout.addWidget(discovered_group)

        # === My Contacts ===
        manual_group = QGroupBox("My Contacts")
        manual_layout = QVBoxLayout()

        self.contacts_list = QListWidget()
        self.contacts_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.contacts_list.customContextMenuRequested.connect(self._show_contacts_menu)
        manual_layout.addWidget(self.contacts_list)

        add_btn = QPushButton("Add Contact Manually")
        add_btn.clicked.connect(self._add_contact)
        manual_layout.addWidget(add_btn)

        manual_group.setLayout(manual_layout)
        layout.addWidget(manual_group)

        self.timer = QTimer()
        self.timer.timeout.connect(self._refresh_discovered)
        self.timer.start(10000)

        self._refresh_discovered()

    def _announce_myself(self):
        if self.rns_node and self.rns_node.announce_myself():
            QMessageBox.information(self, "Announced", "You are now visible on the network.")
        else:
            QMessageBox.warning(self, "Error", "Could not announce (Reticulum not ready).")

    def _refresh_discovered(self):
        self.discovered_list.clear()
        for h, info in self.rns_node.get_discovered_peers():
            display = f"{info.get('name', h[:12])} — last seen {int(time.time() - info.get('last_seen', 0))}s ago"
            self.discovered_list.addItem(display)

    def _show_discovered_menu(self, pos):
        item = self.discovered_list.itemAt(pos)
        if not item:
            return
        row = self.discovered_list.row(item)
        peers = self.rns_node.get_discovered_peers()
        if row >= len(peers):
            return

        h, info = peers[row]

        menu = QMenu(self)
        add_action = QAction("Add to My Contacts", self)
        add_action.triggered.connect(lambda: self._add_discovered_to_contacts(h, info))
        menu.addAction(add_action)

        copy_action = QAction("Copy Hash", self)
        copy_action.triggered.connect(lambda: self._copy_hash(h))
        menu.addAction(copy_action)

        menu.exec(self.discovered_list.viewport().mapToGlobal(pos))

    def _add_discovered_to_contacts(self, h, info):
        name, ok = QInputDialog.getText(self, "Add Contact", "Name for this peer:", text=info.get('name', h[:12]))
        if ok and name:
            self.contacts.append((name, h))
            self._refresh_contacts_list()
            QMessageBox.information(self, "Added", f"Added {name}")

    def _copy_hash(self, h):
        clipboard = QApplication.clipboard()
        clipboard.setText(h)
        QMessageBox.information(self, "Copied", "Hash copied!")

    def _add_contact(self):
        name, ok = QInputDialog.getText(self, "Add Contact", "Contact name:")
        if not ok or not name:
            return
        hash_str, ok = QInputDialog.getText(self, "Add Contact", "Identity hash:")
        if ok and hash_str:
            self.contacts.append((name.strip(), hash_str.strip()))
            self._refresh_contacts_list()

    def _refresh_contacts_list(self):
        self.contacts_list.clear()
        for name, h in self.contacts:
            display = f"{name} — {h[:12]}...{h[-4:] if len(h) > 16 else h}"
            self.contacts_list.addItem(display)

    def _show_contacts_menu(self, pos):
        item = self.contacts_list.itemAt(pos)
        if not item:
            return
        row = self.contacts_list.row(item)
        if row < 0 or row >= len(self.contacts):
            return

        menu = QMenu(self)
        copy_action = QAction("Copy Hash", self)
        copy_action.triggered.connect(lambda: self._copy_hash(self.contacts[row][1]))
        menu.addAction(copy_action)

        delete_action = QAction("Delete Contact", self)
        delete_action.triggered.connect(lambda: self._delete_contact(row))
        menu.addAction(delete_action)

        menu.exec(self.contacts_list.viewport().mapToGlobal(pos))

    def _delete_contact(self, row):
        if 0 <= row < len(self.contacts):
            name, _ = self.contacts.pop(row)
            self._refresh_contacts_list()
            QMessageBox.information(self, "Deleted", f"Removed {name}")
