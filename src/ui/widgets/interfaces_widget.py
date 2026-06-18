"""Dedicated Interfaces tab for advanced Reticulum configuration."""

import RNS
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QGroupBox, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt
from pathlib import Path
import configparser
import shutil


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

        info = QLabel(
            "Edit your Reticulum network interfaces here. "
            "Changes require restarting the application."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Config file info
        self.config_label = QLabel(f"Config file: {self.config_path}")
        self.config_label.setStyleSheet("font-family: monospace; font-size: 11px; color: #aaa;")
        layout.addWidget(self.config_label)

        # Raw config editor
        editor_group = QGroupBox("Current Configuration (edit carefully)")
        editor_layout = QVBoxLayout()

        self.config_editor = QTextEdit()
        self.config_editor.setFontFamily("monospace")
        self.config_editor.setPlainText(self._load_config_text())
        editor_layout.addWidget(self.config_editor)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save Config")
        save_btn.clicked.connect(self._save_config)
        reload_btn = QPushButton("Reload from Disk")
        reload_btn.clicked.connect(self._reload_config)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(reload_btn)
        editor_layout.addLayout(btn_row)

        editor_group.setLayout(editor_layout)
        layout.addWidget(editor_group)

        # Quick Add buttons
        quick_group = QGroupBox("Quick Add Common Interfaces")
        quick_layout = QVBoxLayout()

        auto_btn = QPushButton("Add AutoInterface (recommended for phone + local discovery)")
        auto_btn.clicked.connect(lambda: self._add_interface_template("auto"))
        quick_layout.addWidget(auto_btn)

        tcp_server_btn = QPushButton("Add TCPServerInterface (port 4242)")
        tcp_server_btn.clicked.connect(lambda: self._add_interface_template("tcpserver"))
        quick_layout.addWidget(tcp_server_btn)

        tcp_client_btn = QPushButton("Add TCPClientInterface (connect to another node)")
        tcp_client_btn.clicked.connect(lambda: self._add_interface_template("tcpclient"))
        quick_layout.addWidget(tcp_client_btn)

        quick_group.setLayout(quick_layout)
        layout.addWidget(quick_group)

        # Restart
        restart_btn = QPushButton("Restart Application to Apply Changes")
        restart_btn.setStyleSheet("background-color: #d35400; color: white; font-weight: bold;")
        restart_btn.clicked.connect(self._restart_app)
        layout.addWidget(restart_btn)

        layout.addStretch()

    def _load_config_text(self):
        if self.config_path.exists():
            return self.config_path.read_text()
        else:
            return "# No config file found yet. Reticulum will create one on first run.\n"

    def _reload_config(self):
        self.config_editor.setPlainText(self._load_config_text())

    def _save_config(self):
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(self.config_editor.toPlainText())
            QMessageBox.information(self, "Saved", "Configuration saved. Restart the app to apply changes.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save config:\n{str(e)}")

    def _add_interface_template(self, interface_type):
        current = self.config_editor.toPlainText()

        if interface_type == "auto":
            template = """
[[AutoInterface]]
    interface_enabled = True
"""
        elif interface_type == "tcpserver":
            template = """
[[TCPServerInterface]]
    interface_enabled = True
    listen_port = 4242
"""
        elif interface_type == "tcpclient":
            host, ok = QInputDialog.getText(self, "TCP Client", "Enter host:port to connect to (e.g. 192.168.1.50:4242):")
            if not ok or not host:
                return
            template = f"""
[[TCPClientInterface]]
    interface_enabled = True
    target_host = {host.split(':')[0]}
    target_port = {host.split(':')[1] if ':' in host else '4242'}
"""
        else:
            return

        if template.strip() not in current:
            self.config_editor.append(template)
            QMessageBox.information(self, "Added", f"{interface_type} template added. Edit as needed then Save + Restart.")

    def _restart_app(self):
        from PyQt6.QtWidgets import QApplication
        import os, sys
        if QMessageBox.question(self, "Restart", "Restart now to apply interface changes?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                os.execv(sys.executable, [sys.executable, "-m", "src.main"])
            except:
                QApplication.quit()
