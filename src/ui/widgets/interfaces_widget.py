"""Dedicated Interfaces tab for advanced Reticulum configuration."""

import RNS
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QGroupBox, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt
from pathlib import Path
import configparser


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
            "Advanced interface configuration. Most changes require a full application restart because Reticulum does not support clean in-process restarts."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.config_label = QLabel(f"Config file: {self.config_path}")
        self.config_label.setStyleSheet("font-family: monospace; font-size: 11px; color: #aaa;")
        layout.addWidget(self.config_label)

        # Raw config editor
        editor_group = QGroupBox("Configuration Editor")
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

        # Quick Add
        quick_group = QGroupBox("Quick Add Interfaces")
        quick_layout = QVBoxLayout()

        auto_btn = QPushButton("Add AutoInterface")
        auto_btn.clicked.connect(lambda: self._add_interface_template("auto"))
        quick_layout.addWidget(auto_btn)

        tcp_server_btn = QPushButton("Add TCPServerInterface (port 4242)")
        tcp_server_btn.clicked.connect(lambda: self._add_interface_template("tcpserver"))
        quick_layout.addWidget(tcp_server_btn)

        tcp_client_btn = QPushButton("Add TCPClientInterface")
        tcp_client_btn.clicked.connect(lambda: self._add_interface_template("tcpclient"))
        quick_layout.addWidget(tcp_client_btn)

        quick_group.setLayout(quick_layout)
        layout.addWidget(quick_group)

        # Restart explanation
        restart_group = QGroupBox("Restart Reticulum")
        restart_layout = QVBoxLayout()

        note = QLabel(
            "Reticulum cannot be cleanly restarted from inside the running application without risking instability. "
            "The safest method is to restart the whole application."
        )
        note.setWordWrap(True)
        restart_layout.addWidget(note)

        restart_btn = QPushButton("Restart Application Now (Recommended)")
        restart_btn.setStyleSheet("background-color: #d35400; color: white; font-weight: bold;")
        restart_btn.clicked.connect(self._restart_app)
        restart_layout.addWidget(restart_btn)

        reannounce_btn = QPushButton("Re-Announce Myself + Refresh Peers")
        reannounce_btn.clicked.connect(self._reannounce)
        restart_layout.addWidget(reannounce_btn)

        restart_group.setLayout(restart_layout)
        layout.addWidget(restart_group)

        layout.addStretch()

    def _load_config_text(self):
        if self.config_path.exists():
            return self.config_path.read_text()
        return "# No config file found. Reticulum will create defaults on startup.\n"

    def _reload_config(self):
        self.config_editor.setPlainText(self._load_config_text())

    def _save_config(self):
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(self.config_editor.toPlainText())
            QMessageBox.information(self, "Saved", "Config saved. Restart the app for changes to take effect.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _add_interface_template(self, t):
        current = self.config_editor.toPlainText()
        if t == "auto":
            template = "\n[[AutoInterface]]\n    interface_enabled = True\n"
        elif t == "tcpserver":
            template = "\n[[TCPServerInterface]]\n    interface_enabled = True\n    listen_port = 4242\n"
        elif t == "tcpclient":
            host, ok = QInputDialog.getText(self, "TCP Client", "Host:port to connect to (e.g. 192.168.1.50:4242):")
            if not ok or not host: return
            parts = host.split(":")
            h = parts[0]
            p = parts[1] if len(parts) > 1 else "4242"
            template = f"\n[[TCPClientInterface]]\n    interface_enabled = True\n    target_host = {h}\n    target_port = {p}\n"
        else:
            return

        if template.strip() not in current:
            self.config_editor.append(template)

    def _reannounce(self):
        if self.rns_node and hasattr(self.rns_node, 'announce_myself'):
            success = self.rns_node.announce_myself()
            if success:
                QMessageBox.information(self, "Announced", "Announcement sent. Check Discovered Peers in Contacts tab.")
            else:
                QMessageBox.warning(self, "Error", "Could not announce.")
        else:
            QMessageBox.warning(self, "Error", "Announcement system not available.")

    def _restart_app(self):
        from PyQt6.QtWidgets import QApplication
        import os, sys
        if QMessageBox.question(self, "Restart Application", 
            "Restart the whole application now?\n(This is currently the safest way to reload Reticulum interfaces)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                os.execv(sys.executable, [sys.executable, "-m", "src.main"])
            except:
                QApplication.quit()
