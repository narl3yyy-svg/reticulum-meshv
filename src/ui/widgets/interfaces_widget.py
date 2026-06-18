"""Interfaces tab with link status and restart options."""

import RNS
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QGroupBox, QMessageBox, QLineEdit, QInputDialog
)
from PyQt6.QtCore import Qt
from pathlib import Path
import subprocess


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

        title = QLabel("Reticulum Interfaces & Link Status")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        # === Link Status ===
        status_group = QGroupBox("Link Status (rnstatus)")
        status_layout = QVBoxLayout()

        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        self.status_display.setMaximumHeight(160)
        self.status_display.setFontFamily("monospace")
        status_layout.addWidget(self.status_display)

        status_btns = QHBoxLayout()
        refresh_status_btn = QPushButton("Refresh Link Status")
        refresh_status_btn.clicked.connect(self._refresh_link_status)
        status_btns.addWidget(refresh_status_btn)

        reannounce_btn = QPushButton("Re-Announce Myself")
        reannounce_btn.clicked.connect(self._reannounce)
        status_btns.addWidget(reannounce_btn)
        status_layout.addLayout(status_btns)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # === Direct Connect to Phone ===
        phone_group = QGroupBox("Direct Connect to Android Phone")
        phone_layout = QVBoxLayout()

        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("Phone IP:"))
        self.phone_ip = QLineEdit()
        self.phone_ip.setPlaceholderText("10.10.100.3 or 192.168.x.x")
        ip_layout.addWidget(self.phone_ip)

        ip_layout.addWidget(QLabel("Port:"))
        self.phone_port = QLineEdit("4242")
        self.phone_port.setMaximumWidth(70)
        ip_layout.addWidget(self.phone_port)

        connect_btn = QPushButton("Add TCP Client to Phone")
        connect_btn.clicked.connect(self._connect_to_phone)
        ip_layout.addWidget(connect_btn)

        phone_layout.addLayout(ip_layout)
        phone_group.setLayout(phone_layout)
        layout.addWidget(phone_group)

        # === Config Editor ===
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

        # === Restart Options ===
        restart_group = QGroupBox("Restart Options")
        restart_layout = QVBoxLayout()

        note = QLabel("Reticulum cannot be cleanly restarted from inside the app without risk. Full application restart is safest.")
        note.setWordWrap(True)
        restart_layout.addWidget(note)

        app_restart_btn = QPushButton("Restart Application (Recommended & Safe)")
        app_restart_btn.setStyleSheet("background-color: #d35400; color: white; font-weight: bold;")
        app_restart_btn.clicked.connect(self._restart_app)
        restart_layout.addWidget(app_restart_btn)

        rns_restart_btn = QPushButton("Try Restart Reticulum Only (Experimental)")
        rns_restart_btn.setStyleSheet("background-color: #555555; color: white;")
        rns_restart_btn.clicked.connect(self._try_restart_rns)
        restart_layout.addWidget(rns_restart_btn)

        restart_group.setLayout(restart_layout)
        layout.addWidget(restart_group)

        layout.addStretch()

    def _refresh_link_status(self):
        try:
            result = subprocess.run(["rnstatus"], capture_output=True, text=True, timeout=5)
            output = result.stdout if result.stdout else result.stderr
            # Show only the relevant parts
            lines = output.splitlines()
            filtered = []
            for line in lines:
                if any(x in line for x in ["Interface", "Status", "Peers", "TCP", "AutoInterface"]):
                    filtered.append(line)
            self.status_display.setPlainText("\n".join(filtered) if filtered else output)
        except Exception as e:
            self.status_display.setPlainText(f"Could not get status: {e}")

    def _connect_to_phone(self):
        ip = self.phone_ip.text().strip()
        port = self.phone_port.text().strip()
        if not ip:
            QMessageBox.warning(self, "Error", "Enter phone IP")
            return

        current = self.config_editor.toPlainText()
        if f"target_host = {ip}" in current:
            QMessageBox.information(self, "Exists", "Already connected to this IP.")
            return

        template = f"""
[[TCPClientInterface]]
    type = TCPClientInterface
    interface_enabled = True
    target_host = {ip}
    target_port = {port}
"""
        self.config_editor.append(template)
        QMessageBox.information(self, "Added", "TCP client added. Save + Restart.")

    def _load_config_text(self):
        return self.config_path.read_text() if self.config_path.exists() else "# No config yet\n"

    def _reload_config(self):
        self.config_editor.setPlainText(self._load_config_text())

    def _save_config(self):
        try:
            self.config_path.write_text(self.config_editor.toPlainText())
            QMessageBox.information(self, "Saved", "Saved. Restart app to apply.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _reannounce(self):
        if self.rns_node and self.rns_node.announce_myself():
            QMessageBox.information(self, "Announced", "Announcement sent.")
        else:
            QMessageBox.warning(self, "Error", "Could not announce.")

    def _try_restart_rns(self):
        reply = QMessageBox.question(
            self, "Experimental Restart",
            "Trying to restart only Reticulum inside the app can be unstable.\n\nUse full application restart instead if possible.\n\nTry anyway?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # Best effort soft restart
            if self.rns_node and self.rns_node.reticulum:
                # We can't cleanly restart, so we just re-announce and refresh status
                self.rns_node.announce_myself()
                self._refresh_link_status()
                QMessageBox.information(self, "Done", "Re-announced and refreshed status.\nFor full reload, use 'Restart Application'.")
            else:
                QMessageBox.warning(self, "Not Ready", "Reticulum not initialized.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Soft restart failed: {e}")

    def _restart_app(self):
        if QMessageBox.question(self, "Restart Application", "Restart the whole app now?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            import os, sys
            from PyQt6.QtWidgets import QApplication
            try:
                os.execv(sys.executable, [sys.executable, "-m", "src.main"])
            except:
                QApplication.quit()
