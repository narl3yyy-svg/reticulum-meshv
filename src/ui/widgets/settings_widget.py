"""Settings widget with advanced identity management."""

import RNS
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFileDialog, QCheckBox, QGroupBox, QMessageBox, QTextEdit, QApplication, QInputDialog
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

        # === Identity Management (Improved) ===
        id_group = QGroupBox("Identity Management")
        id_layout = QVBoxLayout()

        self.identity_info = QLabel()
        self.identity_info.setStyleSheet("font-family: monospace; background: #2a2a2a; padding: 8px; border-radius: 4px;")
        self._update_identity_display()
        id_layout.addWidget(self.identity_info)

        btn_row1 = QHBoxLayout()
        new_id_btn = QPushButton("Create New Identity")
        new_id_btn.clicked.connect(self._create_new_identity)
        backup_btn = QPushButton("Backup Current Identity")
        backup_btn.clicked.connect(self._backup_identity)
        btn_row1.addWidget(new_id_btn)
        btn_row1.addWidget(backup_btn)
        id_layout.addLayout(btn_row1)

        btn_row2 = QHBoxLayout()
        load_btn = QPushButton("Load Identity from File...")
        load_btn.clicked.connect(self._load_identity_from_file)
        export_btn = QPushButton("Export Identity")
        export_btn.clicked.connect(self._export_identity)
        btn_row2.addWidget(load_btn)
        btn_row2.addWidget(export_btn)
        id_layout.addLayout(btn_row2)

        note = QLabel("Your identity is permanent. Creating a new one backs up the old one automatically.")
        note.setStyleSheet("color: #888; font-size: 11px;")
        id_layout.addWidget(note)

        id_group.setLayout(id_layout)
        layout.addWidget(id_group)

        # === Status ===
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        status_layout.addWidget(self.status_text)
        refresh_btn = QPushButton("Refresh Status")
        refresh_btn.clicked.connect(self._refresh_status)
        status_layout.addWidget(refresh_btn)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        layout.addStretch()

        self._load_current_interface_settings()
        self._refresh_status()

    def _update_identity_display(self):
        if self.rns_node and self.rns_node.identity:
            short = self.rns_node.get_short_identity_hash()
            full = self.rns_node.get_identity_hash()
            text = f"Current Identity:\nShort: {short}\nFull:  {full}"
            self.identity_info.setText(text)
        else:
            self.identity_info.setText("No identity loaded.")

    def _create_new_identity(self):
        reply = QMessageBox.question(
            self, "Create New Identity",
            "This will back up your current identity and create a new one.\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            identity_path = self.backend.app_config_dir / "identity.key"
            if identity_path.exists():
                backup_path = identity_path.with_suffix(".key.backup")
                shutil.copy2(identity_path, backup_path)

            new_identity = RNS.Identity()
            new_identity.to_file(str(identity_path))

            QMessageBox.information(self, "Success", 
                f"New identity created and old one backed up.\nPlease restart the application.")
            self._update_identity_display()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create new identity:\n{str(e)}")

    def _load_identity_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select identity.key file")
        if not file_path:
            return

        try:
            target = self.backend.app_config_dir / "identity.key"
            shutil.copy2(file_path, target)
            QMessageBox.information(self, "Loaded", "Identity loaded successfully. Please restart.")
            self._update_identity_display()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load identity:\n{str(e)}")

    def _export_identity(self):
        if not self.rns_node or not self.rns_node.identity:
            QMessageBox.warning(self, "Error", "No identity loaded.")
            return

        dest_path, _ = QFileDialog.getSaveFileName(self, "Export identity.key", "identity.key")
        if dest_path:
            try:
                shutil.copy2(self.backend.app_config_dir / "identity.key", dest_path)
                QMessageBox.information(self, "Exported", f"Identity exported to {dest_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

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

    def _refresh_status(self):
        try:
            if self.rns_node and self.rns_node.reticulum:
                text = f"Reticulum running\nIdentity: {self.rns_node.get_short_identity_hash()}\nConfig: {self.rns_node.reticulum.configdir}"
                self.status_text.setPlainText(text)
            else:
                self.status_text.setPlainText("Reticulum not running.")
        except Exception as e:
            self.status_text.setPlainText(str(e))

    def _backup_identity(self):
        src = self.backend.app_config_dir / "identity.key"
        if not src.exists():
            QMessageBox.warning(self, "Error", "No identity file found.")
            return

        dest, _ = QFileDialog.getSaveFileName(self, "Backup identity.key", "identity_backup.key")
        if dest:
            try:
                shutil.copy2(src, dest)
                QMessageBox.information(self, "Backed up", f"Saved to {dest}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
