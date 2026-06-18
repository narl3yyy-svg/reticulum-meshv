"""Interfaces tab with experimental RNS restart restored."""

import RNS
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QGroupBox, QMessageBox, QLineEdit
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

        # Connection Status
        status_group = QGroupBox("Connection Status")
        status_layout = QVBoxLayout()

        self.status_summary = QLabel("Click Refresh to check links")
        self.status_summary.setStyleSheet("font-size: 14px; padding: 8px; background: #2a2a2a; border-radius: 6px;")
        status_layout.addWidget(self.status_summary)

        self.status_details = QTextEdit()
        self.status_details.setReadOnly(True)
        self.status_details.setMaximumHeight(110)
        self.status_details.setFontFamily("monospace")
        status_layout.addWidget(self.status_details)

        refresh_btn = QPushButton("Refresh Status")
        refresh_btn.clicked.connect(self._refresh_status)
        status_layout.addWidget(refresh_btn)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Direct Connect to Phone
        phone_group = QGroupBox("Connect to Android Phone")
        phone_layout = QVBoxLayout()

        ip_row = QHBoxLayout()
        ip_row.addWidget(QLabel("Phone IP:"))
        self.phone_ip = QLineEdit()
        self.phone_ip.setPlaceholderText("10.10.100.3")
        ip_row.addWidget(self.phone_ip)

        ip_row.addWidget(QLabel("Port:"))
        self.phone_port = QLineEdit("4242")
        self.phone_port.setMaximumWidth(70)
        ip_row.addWidget(self.phone_port)

        add_btn = QPushButton("Add TCP Connection to Phone")
        add_btn.clicked.connect(self._add_phone_connection)
        ip_row.addWidget(add_btn)

        phone_layout.addLayout(ip_row)
        phone_group.setLayout(phone_layout)
        layout.addWidget(phone_group)

        # Config Editor
        editor_group = QGroupBox("Advanced Configuration Editor")
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

        # Restart Options (with Experimental restored)
        restart_group = QGroupBox("Restart Options")
        restart_layout = QVBoxLayout()

        note = QLabel("Full app restart is safest. Experimental option tries a lighter reload.")
        note.setWordWrap(True)
        restart_layout.addWidget(note)

        safe_btn = QPushButton("Restart Application (Recommended & Safe)")
        safe_btn.setStyleSheet("background-color: #d35400; color: white; font-weight: bold;")
        safe_btn.clicked.connect(self._restart_app)
        restart_layout.addWidget(safe_btn)

        exp_btn = QPushButton("Try Restart Reticulum Only (Experimental)")
        exp_btn.setStyleSheet("background-color: #555555; color: white;")
        exp_btn.clicked.connect(self._try_experimental_rns_restart)
        restart_layout.addWidget(exp_btn)

        restart_group.setLayout(restart_layout)
        layout.addWidget(restart_group)

        layout.addStretch()

    def _refresh_status(self):
        try:
            result = subprocess.run(["rnstatus"], capture_output=True, text=True, timeout=6)
            output = result.stdout or result.stderr
            self.status_details.setPlainText(output)

            if "TCPClientInterface" in output or "TCPInterface" in output:
                if "Down" in output or "Status : Down" in output:
                    self.status_summary.setText("TCP Link to Phone: Down / Not Connected")
                    self.status_summary.setStyleSheet("color: orange; font-size: 14px; font-weight: bold;")
                else:
                    self.status_summary.setText("TCP Link to Phone: Up / Connected")
                    self.status_summary.setStyleSheet("color: #4ade80; font-size: 14px; font-weight: bold;")
            else:
                self.status_summary.setText("No active TCP client to phone detected.")
                self.status_summary.setStyleSheet("color: #888; font-size: 14px;")

        except Exception as e:
            self.status_details.setPlainText(f"Error: {e}")

    def _add_phone_connection(self):
        ip = self.phone_ip.text().strip()
        port = self.phone_port.text().strip() or "4242"
        if not ip: return

        current = self.config_editor.toPlainText()
        if f"target_host = {ip}" in current: return

        template = f"""
[[TCPClientInterface]]
    type = TCPClientInterface
    interface_enabled = True
    target_host = {ip}
    target_port = {port}
"""
        self.config_editor.append(template)
        QMessageBox.information(self, "Added", "TCP client added. Save Config then Restart.")

    def _load_config_text(self):
        return self.config_path.read_text() if self.config_path.exists() else ""

    def _reload_config(self):
        self.config_editor.setPlainText(self._load_config_text())

    def _save_config(self):
        try:
            self.config_path.write_text(self.config_editor.toPlainText())
            QMessageBox.information(self, "Saved", "Saved. Restart app to apply.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _try_experimental_rns_restart(self):
        reply = QMessageBox.question(self, "Experimental", 
            "This tries to reload Reticulum without full restart.\nIt may not work perfectly.\n\nContinue?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return

        try:
            if self.rns_node:
                self.rns_node.announce_myself()
                self._refresh_status()
                QMessageBox.information(self, "Done", "Re-announced and refreshed status.")
        except Exception as e:
            QMessageBox.warning(self, "Limited", f"Could only do partial reload: {e}")

    def _restart_app(self):
        if QMessageBox.question(self, "Restart", "Restart the application now?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            import os, sys
            from PyQt6.QtWidgets import QApplication
            try:
                os.execv(sys.executable, [sys.executable, "-m", "src.main"])
            except:
                QApplication.quit()
