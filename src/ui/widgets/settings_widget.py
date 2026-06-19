"""Settings widget with identity hash display and announce button."""

import RNS
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFileDialog, QCheckBox, QGroupBox, QMessageBox, QTextEdit, QApplication
)
from PyQt6.QtCore import Qt
from pathlib import Path
import sys
import os
import shutil
import configparser


class SettingsWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.rns_node = backend.rns_node
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        # === Identity Section ===
        id_group = QGroupBox("Your Identity")
        id_layout = QVBoxLayout()

        self.identity_label = QLabel()
        self.identity_label.setStyleSheet("font-family: monospace; background: #2a2a2a; padding: 10px; border-radius: 6px; font-size: 12px;")
        self._update_identity_display()
        id_layout.addWidget(self.identity_label)

        announce_btn = QPushButton("Announce Myself on Network")
        announce_btn.clicked.connect(self._announce_myself)
        id_layout.addWidget(announce_btn)

        note = QLabel("Announcing makes you visible to other nodes on the Reticulum network.")
        note.setStyleSheet("color: #888; font-size: 11px;")
        id_layout.addWidget(note)

        id_group.setLayout(id_layout)
        layout.addWidget(id_group)

        # === Downloads ===
        dl_group = QGroupBox("File Downloads")
        dl_layout = QVBoxLayout()

        self.download_path = QLineEdit()
        self.download_path.setReadOnly(True)
        if hasattr(self.backend, 'downloads_dir'):
            self.download_path.setText(str(self.backend.downloads_dir))

        browse_btn = QPushButton("Change Download Folder...")
        browse_btn.clicked.connect(self._change_download_folder)

        dl_layout.addWidget(QLabel("Received files & extracted folders are saved to:"))
        dl_layout.addWidget(self.download_path)
        dl_layout.addWidget(browse_btn)
        dl_group.setLayout(dl_layout)
        layout.addWidget(dl_group)

        # === Interfaces ===
        iface_group = QGroupBox("Reticulum Interfaces")
        iface_layout = QVBoxLayout()

        self.config_path_label = QLabel(f"Config: {Path.home() / '.reticulum' / 'config'}")
        self.config_path_label.setStyleSheet("font-family: monospace; font-size: 11px;")
        iface_layout.addWidget(self.config_path_label)

        self.auto_interface_cb = QCheckBox("AutoInterface enabled")
        self.auto_interface_cb.setChecked(True)
        iface_layout.addWidget(self.auto_interface_cb)

        tcp_layout = QHBoxLayout()
        self.tcp_server_cb = QCheckBox("TCPServer on port:")
        self.tcp_port = QLineEdit("4242")
        self.tcp_port.setMaximumWidth(80)
        tcp_layout.addWidget(self.tcp_server_cb)
        tcp_layout.addWidget(self.tcp_port)
        tcp_layout.addStretch()
        iface_layout.addLayout(tcp_layout)

        save_iface_btn = QPushButton("Save Interface Settings")
        save_iface_btn.clicked.connect(self._save_interface_settings)
        iface_layout.addWidget(save_iface_btn)

        restart_btn = QPushButton("Restart Application Now")
        restart_btn.setStyleSheet("background-color: #d35400; color: white; font-weight: bold;")
        restart_btn.clicked.connect(self._restart_application)
        iface_layout.addWidget(restart_btn)

        iface_group.setLayout(iface_layout)
        layout.addWidget(iface_group)

        layout.addStretch()

        self._load_current_interface_settings()

    def _update_identity_display(self):
        if self.rns_node and self.rns_node.identity:
            try:
                full_hash = self.rns_node.get_identity_hash()
                text = f"Your Identity Hash:\n{full_hash}"
                self.identity_label.setText(text)
            except:
                self.identity_label.setText("Could not load identity hash.")
        else:
            self.identity_label.setText("Identity not loaded.")

    def _announce_myself(self):
        if self.rns_node and self.rns_node.announce_myself():
            QMessageBox.information(self, "Announced", "You are now visible on the Reticulum network.")
        else:
            QMessageBox.warning(self, "Error", "Could not announce (Reticulum not ready).")

    def _save_interface_settings(self):
        config_path = Path.home() / ".reticulum" / "config"
        parser = configparser.ConfigParser()
        if config_path.exists():
            parser.read(config_path)

        if not parser.has_section("interfaces"):
            parser.add_section("interfaces")

        auto_sec = "interfaces.AutoInterface"
        if not parser.has_section(auto_sec):
            parser.add_section(auto_sec)
        parser.set(auto_sec, "interface_enabled", str(self.auto_interface_cb.isChecked()))

        tcp_sec = "interfaces.TCPServerInterface"
        if not parser.has_section(tcp_sec):
            parser.add_section(tcp_sec)
        parser.set(tcp_sec, "interface_enabled", str(self.tcp_server_cb.isChecked()))
        parser.set(tcp_sec, "listen_port", self.tcp_port.text().strip())

        try:
            with open(config_path, "w") as f:
                parser.write(f)
            QMessageBox.information(self, "Saved", "Interface settings saved. Restart to apply.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _load_current_interface_settings(self):
        config_path = Path.home() / ".reticulum" / "config"
        if not config_path.exists():
            return
        try:
            parser = configparser.ConfigParser()
            parser.read(config_path)
            if parser.has_section("interfaces.AutoInterface"):
                enabled = parser.getboolean("interfaces.AutoInterface", "interface_enabled", fallback=True)
                self.auto_interface_cb.setChecked(enabled)
            if parser.has_section("interfaces.TCPServerInterface"):
                enabled = parser.getboolean("interfaces.TCPServerInterface", "interface_enabled", fallback=False)
                port = parser.get("interfaces.TCPServerInterface", "listen_port", fallback="4242")
                self.tcp_server_cb.setChecked(enabled)
                self.tcp_port.setText(str(port))
        except:
            pass

    def _change_download_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose download folder")
        if folder:
            self.download_path.setText(folder)
            if hasattr(self.backend, 'downloads_dir'):
                self.backend.downloads_dir = Path(folder)

    def _restart_application(self):
        if QMessageBox.question(self, "Restart", "Restart application now?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                os.execv(sys.executable, [sys.executable, "-m", "src.main"])
            except:
                QApplication.quit()
