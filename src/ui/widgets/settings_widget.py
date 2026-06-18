"""Settings widget with Interfaces configuration."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFileDialog, QCheckBox, QGroupBox, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt
from pathlib import Path
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
        iface_group = QGroupBox("Reticulum Interfaces & Connectivity")
        iface_layout = QVBoxLayout()

        iface_info = QLabel(
            "Reticulum reads its interface configuration from <b>~/.reticulum/config</b>.<br>"
            "You can edit it manually or use the options below for common setups."
        )
        iface_info.setWordWrap(True)
        iface_layout.addWidget(iface_info)

        # Show current config path
        config_path = Path.home() / ".reticulum" / "config"
        self.config_path_label = QLabel(f"Config file: {config_path}")
        self.config_path_label.setStyleSheet("font-family: monospace; font-size: 11px; color: #aaa;")
        iface_layout.addWidget(self.config_path_label)

        # Common interfaces
        self.auto_interface_cb = QCheckBox("Enable AutoInterface (recommended for local/WiFi/Bluetooth discovery)")
        self.auto_interface_cb.setChecked(True)
        iface_layout.addWidget(self.auto_interface_cb)

        # TCP Server option
        tcp_layout = QHBoxLayout()
        self.tcp_server_cb = QCheckBox("Run TCP Server on port:")
        self.tcp_port = QLineEdit("4242")
        self.tcp_port.setMaximumWidth(80)
        tcp_layout.addWidget(self.tcp_server_cb)
        tcp_layout.addWidget(self.tcp_port)
        tcp_layout.addStretch()
        iface_layout.addLayout(tcp_layout)

        apply_btn = QPushButton("Apply Interface Changes (requires restart)")
        apply_btn.clicked.connect(self._apply_interface_changes)
        iface_layout.addWidget(apply_btn)

        note = QLabel(
            "<b>Tip for Android phone:</b> Install Sideband or another Reticulum app on your phone. "
            "Use the same WiFi network and enable AutoInterface on both devices, or set up a TCP connection. "
            "After announcing on one device, the other should discover it in the Contacts tab."
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

        # Identity section (existing)
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

        # Initial status refresh
        self._refresh_status()

    def _change_download_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose download folder")
        if folder:
            self.download_path.setText(folder)
            if hasattr(self.backend, 'downloads_dir'):
                self.backend.downloads_dir = Path(folder)
            QMessageBox.information(self, "Updated", "Download folder changed.")

    def _apply_interface_changes(self):
        # This is a simplified version. For full control, edit ~/.reticulum/config manually.
        config_path = Path.home() / ".reticulum" / "config"
        QMessageBox.information(
            self,
            "Interface Changes",
            "To apply interface changes, please edit the config file manually:\n\n" + str(config_path) + 
            "\n\nCommon sections:\n[interfaces]\n  [[AutoInterface]]\n  interface_enabled = True\n\n  [[TCPServerInterface]]\n  interface_enabled = True\n  listen_port = 4242\n\nThen restart the application."
        )

    def _refresh_status(self):
        try:
            if self.rns_node and self.rns_node.reticulum:
                reticulum = self.rns_node.reticulum
                status = f"Reticulum running\n"
                status += f"Identity: {self.rns_node.get_short_identity_hash()}\n"
                status += f"Config dir: {reticulum.configdir}\n\n"
                status += "Interfaces are configured in ~/.reticulum/config\n"
                status += "Check the file for active interfaces and ports.\n"
                self.status_text.setPlainText(status)
            else:
                self.status_text.setPlainText("Reticulum not initialized.")
        except Exception as e:
            self.status_text.setPlainText(f"Error getting status: {str(e)}")

    def _backup_identity(self):
        QMessageBox.information(
            self,
            "Backup Identity",
            "Your identity.key file is at:\n\n" + str(self.backend.app_config_dir / "identity.key") + 
            "\n\nCopy this file to back up your permanent mesh identity."
        )
