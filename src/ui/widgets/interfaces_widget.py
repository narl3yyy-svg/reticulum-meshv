"""Dedicated Interfaces tab - improved for direct phone connection."""

import RNS
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QGroupBox, QMessageBox, QLineEdit, QInputDialog
)
from PyQt6.QtCore import Qt
from pathlib import Path


class InterfacesWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.rns_node = backend.rns_node
        self.config_path = Path.home() / ".reticulum" / "config"
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Reticulum Interfaces")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        # === Direct Connect to Phone ===
        phone_group = QGroupBox("Direct Connect to Android MeshChatX / Sideband")
        phone_layout = QVBoxLayout()

        phone_info = QLabel(
            "Easiest reliable method: Connect directly to your phone via TCP.\n"
            "Enter your phone's local IP below (find it in phone's WiFi settings or MeshChatX)."
        )
        phone_info.setWordWrap(True)
        phone_layout.addWidget(phone_info)

        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("Phone IP:"))
        self.phone_ip = QLineEdit()
        self.phone_ip.setPlaceholderText("192.168.1.XXX")
        ip_layout.addWidget(self.phone_ip)

        ip_layout.addWidget(QLabel("Port:"))
        self.phone_port = QLineEdit("4242")
        self.phone_port.setMaximumWidth(80)
        ip_layout.addWidget(self.phone_port)

        connect_btn = QPushButton("Connect to Phone (Add TCP Client)")
        connect_btn.setStyleSheet("font-weight: bold;")
        connect_btn.clicked.connect(self._connect_to_phone)
        ip_layout.addWidget(connect_btn)

        phone_layout.addLayout(ip_layout)

        note = QLabel("After adding, Save Config → Restart Application. Then try announcing again.")
        note.setStyleSheet("color: #888; font-size: 11px;")
        phone_layout.addWidget(note)

        phone_group.setLayout(phone_layout)
        layout.addWidget(phone_group)

        # === Current Config Editor ===
        editor_group = QGroupBox("Full Configuration (Advanced)")
        editor_layout = QVBoxLayout()

        self.config_editor = QTextEdit()
        self.config_editor.setFontFamily("monospace")
        self.config_editor.setPlainText(self._load_config_text())
        editor_layout.addWidget(self.config_editor)

        btns = QHBoxLayout()
        save_btn = QPushButton("Save Config")
        save_btn.clicked.connect(self._save_config)
        reload_btn = QPushButton("Reload")
        reload_btn.clicked.connect(self._reload_config)
        btns.addWidget(save_btn)
        btns.addWidget(reload_btn)
        editor_layout.addLayout(btns)

        editor_group.setLayout(editor_layout)
        layout.addWidget(editor_group)

        # Quick Add
        quick_group = QGroupBox("Quick Add Other Interfaces")
        quick_layout = QVBoxLayout()

        auto_btn = QPushButton("Add/Enable AutoInterface")
        auto_btn.clicked.connect(lambda: self._add_interface_template("auto"))
        quick_layout.addWidget(auto_btn)

        udp_btn = QPushButton("Add UDPInterface (sometimes more reliable than Auto)")
        udp_btn.clicked.connect(lambda: self._add_interface_template("udp"))
        quick_layout.addWidget(udp_btn)

        quick_group.setLayout(quick_layout)
        layout.addWidget(quick_group)

        # Restart
        restart_btn = QPushButton("Restart Application Now")
        restart_btn.setStyleSheet("background-color: #d35400; color: white; font-weight: bold;")
        restart_btn.clicked.connect(self._restart_app)
        layout.addWidget(restart_btn)

        reannounce_btn = QPushButton("Re-Announce + Refresh Discovered Peers")
        reannounce_btn.clicked.connect(self._reannounce)
        layout.addWidget(reannounce_btn)

        layout.addStretch()

    def _connect_to_phone(self):
        ip = self.phone_ip.text().strip()
        port = self.phone_port.text().strip()

        if not ip:
            QMessageBox.warning(self, "Error", "Please enter your phone's IP address.")
            return

        current = self.config_editor.toPlainText()

        # Check if already exists
        if f"target_host = {ip}" in current:
            QMessageBox.information(self, "Already Exists", "A TCP client to this IP already exists in the config.")
            return

        template = f"""
[[TCPClientInterface]]
    interface_enabled = True
    target_host = {ip}
    target_port = {port}
"""

        self.config_editor.append(template)
        QMessageBox.information(self, "Added", 
            f"TCP Client to phone ({ip}:{port}) added.\nClick Save Config → Restart Application.")

    def _load_config_text(self):
        if self.config_path.exists():
            return self.config_path.read_text()
        return "# No config file found yet.\n"

    def _reload_config(self):
        self.config_editor.setPlainText(self._load_config_text())

    def _save_config(self):
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(self.config_editor.toPlainText())
            QMessageBox.information(self, "Saved", "Configuration saved. Please restart the application.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _add_interface_template(self, t):
        current = self.config_editor.toPlainText()
        if t == "auto":
            template = "\n[[AutoInterface]]\n    interface_enabled = True\n"
        elif t == "udp":
            template = "\n[[UDPInterface]]\n    interface_enabled = True\n    listen_ip = 0.0.0.0\n    listen_port = 0\n"
        else:
            return

        if template.strip() not in current:
            self.config_editor.append(template)

    def _reannounce(self):
        if self.rns_node and hasattr(self.rns_node, "announce_myself"):
            if self.rns_node.announce_myself():
                QMessageBox.information(self, "Announced", "Announcement sent. Check Contacts → Discovered Peers.")
            else:
                QMessageBox.warning(self, "Failed", "Could not send announcement.")
        else:
            QMessageBox.warning(self, "Error", "Announcement system not ready.")

    def _restart_app(self):
        from PyQt6.QtWidgets import QApplication
        import os, sys
        if QMessageBox.question(self, "Restart", "Restart application now?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                os.execv(sys.executable, [sys.executable, "-m", "src.main"])
            except:
                QApplication.quit()
