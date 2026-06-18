"""Settings widget with actual interface config saving."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFileDialog, QCheckBox, QGroupBox, QMessageBox, QTextEdit, QApplication
)
from PyQt6.QtCore import Qt
from pathlib import Path
import sys
import os
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

        # === Interfaces (now actually saves) ===
        iface_group = QGroupBox("Reticulum Interfaces & Connectivity")
        iface_layout = QVBoxLayout()

        iface_info = QLabel(
            "Configure common Reticulum interfaces. Changes are saved to <b>~/.reticulum/config</b>."
        )
        iface_info.setWordWrap(True)
        iface_layout.addWidget(iface_info)

        config_path = Path.home() / ".reticulum" / "config"
        self.config_path_label = QLabel(f"Config file: {config_path}")
        self.config_path_label.setStyleSheet("font-family: monospace; font-size: 11px; color: #aaa;")
        iface_layout.addWidget(self.config_path_label)

        self.auto_interface_cb = QCheckBox("Enable AutoInterface (recommended for WiFi + phone discovery)")
        self.auto_interface_cb.setChecked(True)
        iface_layout.addWidget(self.auto_interface_cb)

        tcp_layout = QHBoxLayout()
        self.tcp_server_cb = QCheckBox("Enable TCP Server on port:")
        self.tcp_port = QLineEdit("4242")
        self.tcp_port.setMaximumWidth(80)
        tcp_layout.addWidget(self.tcp_server_cb)
        tcp_layout.addWidget(self.tcp_port)
        tcp_layout.addStretch()
        iface_layout.addLayout(tcp_layout)

        apply_btn = QPushButton("Save Interface Settings")
        apply_btn.setStyleSheet("font-weight: bold;")
        apply_btn.clicked.connect(self._save_interface_settings)
        iface_layout.addWidget(apply_btn)

        restart_btn = QPushButton("Restart Application Now")
        restart_btn.setStyleSheet("background-color: #d35400; color: white; font-weight: bold;")
        restart_btn.clicked.connect(self._restart_application)
        iface_layout.addWidget(restart_btn)

        note = QLabel(
            "<b>Connecting to Android phone:</b> Enable AutoInterface on both devices on the same WiFi, "
            "or enable TCP Server here and connect from Sideband as a TCP client."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #ccc; font-size: 11px; margin-top: 8px;")
        iface_layout.addWidget(note)

        iface_group.setLayout(iface_layout)
        layout.addWidget(iface_group)

        # === Current Status ===
        status_group = QGroupBox("Current Reticulum Status")
        status_layout = QVBoxLayout()

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(120)
        status_layout.addWidget(self.status_text)

        refresh_status_btn = QPushButton("Refresh Status")
        refresh_status_btn.clicked.connect(self._refresh_status)
        status_layout.addWidget(refresh_status_btn)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Identity
        id_group = QGroupBox("Identity")
        id_layout = QVBoxLayout()

        backup_btn = QPushButton("Backup Identity (copy identity.key)")
        backup_btn.clicked.connect(self._backup_identity)

        id_layout.addWidget(QLabel("Your permanent mesh identity is stored in:"))
        id_layout.addWidget(QLabel(str(self.backend.app_config_dir / "identity.key")))
        id_layout.addWidget(backup_btn)
        id_group.setLayout(id_layout)
        layout.addWidget(id_group)

        layout.addStretch()

        self._load_current_interface_settings()
        self._refresh_status()

    def _load_current_interface_settings(self):
        """Try to read current settings from config file."""
        config_path = Path.home() / ".reticulum" / "config"
        if not config_path.exists():
            return

        try:
            parser = configparser.ConfigParser()
            parser.read(config_path)

            # AutoInterface
            if parser.has_section("interfaces") and parser.has_section("interfaces.AutoInterface"):
                enabled = parser.getboolean("interfaces.AutoInterface", "interface_enabled", fallback=True)
                self.auto_interface_cb.setChecked(enabled)

            # TCP Server
            if parser.has_section("interfaces") and parser.has_section("interfaces.TCPServerInterface"):
                enabled = parser.getboolean("interfaces.TCPServerInterface", "interface_enabled", fallback=False)
                port = parser.get("interfaces.TCPServerInterface", "listen_port", fallback="4242")
                self.tcp_server_cb.setChecked(enabled)
                self.tcp_port.setText(port)
        except Exception:
            pass

    def _save_interface_settings(self):
        config_path = Path.home() / ".reticulum" / "config"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        parser = configparser.ConfigParser()
        if config_path.exists():
            parser.read(config_path)

        if not parser.has_section("interfaces"):
            parser.add_section("interfaces")

        # AutoInterface
        auto_section = "interfaces.AutoInterface"
        if not parser.has_section(auto_section):
            parser.add_section(auto_section)
        parser.set(auto_section, "interface_enabled", str(self.auto_interface_cb.isChecked()))

        # TCPServerInterface
        tcp_section = "interfaces.TCPServerInterface"
        if not parser.has_section(tcp_section):
            parser.add_section(tcp_section)
        parser.set(tcp_section, "interface_enabled", str(self.tcp_server_cb.isChecked()))
        parser.set(tcp_section, "listen_port", self.tcp_port.text().strip())

        try:
            with open(config_path, "w") as f:
                parser.write(f)
            QMessageBox.information(self, "Saved", 
                "Interface settings saved.\nPlease restart the application for changes to take effect.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save config:\n{str(e)}")

    def _change_download_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose download folder")
        if folder:
            self.download_path.setText(folder)
            if hasattr(self.backend, 'downloads_dir'):
                self.backend.downloads_dir = Path(folder)
            QMessageBox.information(self, "Updated", "Download folder changed.")

    def _restart_application(self):
        reply = QMessageBox.question(
            self,
            "Restart Application",
            "Restart now to apply interface changes?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                python = sys.executable
                os.execv(python, [python, "-m", "src.main"])
            except Exception as e:
                QMessageBox.critical(self, "Restart Failed", f"Please restart manually with: python -m src.main\n\n{e}")
                QApplication.quit()

    def _refresh_status(self):
        try:
            if self.rns_node and self.rns_node.reticulum:
                reticulum = self.rns_node.reticulum
                status = f"Reticulum running\n"
                status += f"Identity: {self.rns_node.get_short_identity_hash()}\n"
                status += f"Config dir: {reticulum.configdir}\n\n"
                status += "Check ~/.reticulum/config for active interfaces and ports."
                self.status_text.setPlainText(status)
            else:
                self.status_text.setPlainText("Reticulum not initialized.")
        except Exception as e:
            self.status_text.setPlainText(f"Error: {str(e)}")

    def _backup_identity(self):
        QMessageBox.information(
            self,
            "Backup Identity",
            "Your identity.key is at:\n\n" + str(self.backend.app_config_dir / "identity.key")
        )
