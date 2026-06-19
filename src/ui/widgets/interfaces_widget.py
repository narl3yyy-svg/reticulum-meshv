"""Interfaces tab — node setup, status, and config editor popup."""

import RNS
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QGroupBox, QMessageBox, QLineEdit, QDialog
)
from PyQt6.QtCore import Qt
from pathlib import Path
from src.config.theme import MeshTheme
from src.ui.widgets.common import StatusDot


class ConfigEditorDialog(QDialog):
    def __init__(self, config_path, parent=None):
        super().__init__(parent)
        self.config_path = config_path
        self.setWindowTitle("Reticulum Configuration Editor")
        self.setMinimumSize(700, 500)
        self.setStyleSheet(f"background-color: {MeshTheme.CANVAS};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel("Advanced Configuration Editor")
        header.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {MeshTheme.TEXT}; background: transparent;")
        layout.addWidget(header)

        warning = QLabel("Editing this file directly can break RNS if malformed. Restart app after saving.")
        warning.setWordWrap(True)
        warning.setStyleSheet(f"color: {MeshTheme.WARNING}; font-size: 12px; background: transparent;")
        layout.addWidget(warning)

        self.editor = QTextEdit()
        self.editor.setStyleSheet(f"font-family: 'JetBrains Mono', monospace; color: {MeshTheme.TEXT}; background: {MeshTheme.SURFACE}; border: 1px solid {MeshTheme.BORDER}; border-radius: 12px; padding: 8px; font-size: 13px;")
        self.editor.setPlainText(self._load())
        layout.addWidget(self.editor)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        reload_btn = QPushButton("Reload from File")
        reload_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {MeshTheme.TEXT_MUTED};
                border: 1px solid {MeshTheme.BORDER}; border-radius: 12px; padding: 10px 20px; }}
            QPushButton:hover {{ background-color: {MeshTheme.SURFACE_VARIANT}; color: {MeshTheme.TEXT}; }}
        """)
        reload_btn.clicked.connect(self._reload)
        btn_row.addWidget(reload_btn)

        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {MeshTheme.TEXT_MUTED};
                border: 1px solid {MeshTheme.BORDER}; border-radius: 12px; padding: 10px 20px; }}
            QPushButton:hover {{ background-color: {MeshTheme.SURFACE_VARIANT}; color: {MeshTheme.TEXT}; }}
        """)
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _load(self):
        return self.config_path.read_text() if self.config_path.exists() else "# No config file found"

    def _reload(self):
        self.editor.setPlainText(self._load())

    def _save(self):
        try:
            self.config_path.write_text(self.editor.toPlainText())
            QMessageBox.information(self, "Saved", "Config saved. Restart app to apply.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class InterfacesWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.rns_node = getattr(backend, 'rns_node', None)
        self.config_path = Path.home() / ".reticulum" / "config"
        self.init_ui()
        self._refresh_status()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Interfaces")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {MeshTheme.TEXT}; background: transparent;")
        layout.addWidget(title)

        def group_style():
            return f"""
                QGroupBox {{ color: {MeshTheme.TEXT_MUTED}; font-size: 12px;
                    border: 1px solid {MeshTheme.BORDER_CARD}; border-radius: 16px; margin-top: 20px;
                    padding: 16px; }}
                QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left;
                    padding: 4px 12px; color: {MeshTheme.TEXT_MUTED}; font-size: 12px; }}
            """

        # === Node Setup ===
        node_group = QGroupBox("This Node Setup")
        node_group.setStyleSheet(group_style())
        node_layout = QVBoxLayout()

        node_desc = QLabel(
            "This desktop is configured as a central node.\n"
            "Phones running MeshChatX connect to it via TCP Client on port 4242."
        )
        node_desc.setWordWrap(True)
        node_desc.setStyleSheet(f"color: {MeshTheme.TEXT_MUTED}; font-size: 13px; background: transparent;")
        node_layout.addWidget(node_desc)

        your_ip = QLabel("Your IP addresses on this network:")
        your_ip.setStyleSheet(f"color: {MeshTheme.TEXT}; font-weight: 600; background: transparent; margin-top: 8px;")
        node_layout.addWidget(your_ip)

        try:
            import socket
            ips = []
            try:
                ips = socket.gethostbyname_ex(socket.gethostname())[2]
            except:
                pass
            if not ips:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    s.connect(("8.8.8.8", 80))
                    ips = [s.getsockname()[0]]
                except:
                    ips = ["127.0.0.1"]
                finally:
                    s.close()
            for ip in set(ips):
                ip_label = QLabel(f"  {ip}:4242")
                ip_label.setStyleSheet(f"font-family: 'JetBrains Mono', monospace; font-size: 14px; color: {MeshTheme.ACCENT}; background: transparent; padding: 2px 0;")
                node_layout.addWidget(ip_label)
        except:
            pass

        phone_info = QLabel(
            "\nOn your phone (MeshChatX), go to Interfaces > Add > TCP Client:\n"
            "  Host: <one of the IPs above>   Port: 4242"
        )
        phone_info.setWordWrap(True)
        phone_info.setStyleSheet(f"color: {MeshTheme.TEXT_MUTED}; font-size: 12px; background: transparent;")
        node_layout.addWidget(phone_info)

        node_group.setLayout(node_layout)
        layout.addWidget(node_group)

        # === Connection Status ===
        status_group = QGroupBox("Connection Status")
        status_group.setStyleSheet(group_style())
        status_layout = QVBoxLayout()

        status_row = QHBoxLayout()
        self.status_dot = StatusDot(StatusDot.UNKNOWN, 12)
        self.status_dot.setStyleSheet("background: transparent;")
        status_row.addWidget(self.status_dot)
        self.status_summary = QLabel("Checking...")
        self.status_summary.setStyleSheet(f"font-size: 14px; padding: 8px 14px; background: {MeshTheme.SURFACE_VARIANT}; border-radius: 12px; color: {MeshTheme.TEXT};")
        status_row.addWidget(self.status_summary, 1)
        status_layout.addLayout(status_row)

        self.status_details = QTextEdit()
        self.status_details.setReadOnly(True)
        self.status_details.setMaximumHeight(160)
        self.status_details.setStyleSheet(f"font-family: 'JetBrains Mono', monospace; color: {MeshTheme.TEXT}; background: {MeshTheme.SURFACE_VARIANT}; border: none; border-radius: 12px; padding: 10px; font-size: 12px;")
        status_layout.addWidget(self.status_details)

        refresh_btn = QPushButton("Refresh Status")
        refresh_btn.clicked.connect(self._refresh_status)
        status_layout.addWidget(refresh_btn)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # === Connect to Phone ===
        phone_group = QGroupBox("Connect to a Phone")
        phone_group.setStyleSheet(group_style())
        phone_layout = QVBoxLayout()

        phone_desc = QLabel("Add a TCP Client interface to connect to a phone running MeshChatX as a server:")
        phone_desc.setWordWrap(True)
        phone_desc.setStyleSheet(f"color: {MeshTheme.TEXT_MUTED}; font-size: 12px; background: transparent;")
        phone_layout.addWidget(phone_desc)

        ip_row = QHBoxLayout()
        ip_row.addWidget(QLabel("Phone IP:"))
        self.phone_ip = QLineEdit()
        self.phone_ip.setPlaceholderText("10.10.100.11")
        self.phone_ip.setMaximumWidth(160)
        ip_row.addWidget(self.phone_ip)

        ip_row.addWidget(QLabel("Port:"))
        self.phone_port = QLineEdit("4242")
        self.phone_port.setMaximumWidth(70)
        ip_row.addWidget(self.phone_port)

        add_btn = QPushButton("Add to Config")
        add_btn.clicked.connect(self._add_phone_connection)
        ip_row.addWidget(add_btn)

        phone_layout.addLayout(ip_row)
        phone_group.setLayout(phone_layout)
        layout.addWidget(phone_group)

        # === Config Editor Button ===
        config_group = QGroupBox("Advanced Configuration")
        config_group.setStyleSheet(group_style())
        config_layout = QVBoxLayout()

        config_desc = QLabel("Edit the raw Reticulum configuration file. Opens in a separate window.")
        config_desc.setWordWrap(True)
        config_desc.setStyleSheet(f"color: {MeshTheme.TEXT_MUTED}; font-size: 12px; background: transparent;")
        config_layout.addWidget(config_desc)

        open_editor_btn = QPushButton("Open Config Editor")
        open_editor_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {MeshTheme.ACCENT};
                border: 1px solid {MeshTheme.ACCENT}; border-radius: 12px;
                padding: 10px 20px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background-color: {MeshTheme.ACCENT}20; }}
        """)
        open_editor_btn.clicked.connect(self._open_config_editor)
        config_layout.addWidget(open_editor_btn)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # === Restart ===
        restart_group = QGroupBox("Restart")
        restart_group.setStyleSheet(group_style())
        restart_layout = QVBoxLayout()

        restart_btn = QPushButton("Restart Application")
        restart_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {MeshTheme.WARNING}; color: white; border: none;
                border-radius: 12px; padding: 10px 20px; font-size: 14px; font-weight: 600; }}
            QPushButton:hover {{ background-color: #f97316; }}
        """)
        restart_btn.clicked.connect(self._restart_app)
        restart_layout.addWidget(restart_btn)

        restart_group.setLayout(restart_layout)
        layout.addWidget(restart_group)

        layout.addStretch()

        # Auto-refresh timer
        from PyQt6.QtCore import QTimer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_status)
        self._timer.start(10000)

    def _refresh_status(self):
        try:
            ifaces = []
            if self.rns_node and self.rns_node.reticulum:
                ifaces = self.rns_node.get_interfaces()

            if not ifaces:
                self.status_details.setPlainText("No interfaces found. Check your RNS config.")
                self.status_summary.setText("No interfaces")
                self.status_dot.set_color(MeshTheme.TEXT_DIM)
                return

            lines = []
            up_count = 0
            down_count = 0
            for iface in ifaces:
                name = iface.get("name", "unknown")
                itype = iface.get("type", "?")
                online = iface.get("online", False)
                status = "Up" if online else "Down"
                if online:
                    up_count += 1
                else:
                    down_count += 1
                bi = iface.get("bytes_in", 0)
                bo = iface.get("bytes_out", 0)
                lines.append(f"{name} [{itype}]: {status}  RX={bi} TX={bo}")

            self.status_details.setPlainText("\n".join(lines))

            total = len(ifaces)
            if down_count > 0 and up_count == 0:
                self.status_summary.setText(f"All {total} interface(s) down")
                self.status_summary.setStyleSheet(f"color: {MeshTheme.ERROR}; font-size: 14px; font-weight: 600; padding: 8px 14px; background: {MeshTheme.SURFACE_VARIANT}; border-radius: 12px;")
                self.status_dot.set_color(MeshTheme.ERROR)
            elif down_count > 0:
                self.status_summary.setText(f"{up_count} up, {down_count} down ({total} total)")
                self.status_summary.setStyleSheet(f"color: {MeshTheme.WARNING}; font-size: 14px; font-weight: 600; padding: 8px 14px; background: {MeshTheme.SURFACE_VARIANT}; border-radius: 12px;")
                self.status_dot.set_color(MeshTheme.WARNING)
            else:
                self.status_summary.setText(f"All {up_count} interface(s) up")
                self.status_summary.setStyleSheet(f"color: {MeshTheme.SUCCESS}; font-size: 14px; font-weight: 600; padding: 8px 14px; background: {MeshTheme.SURFACE_VARIANT}; border-radius: 12px;")
                self.status_dot.set_color(MeshTheme.SUCCESS)

        except Exception as e:
            self.status_details.setPlainText(f"Error: {e}")
            self.status_dot.set_color(MeshTheme.TEXT_DIM)

    def _add_phone_connection(self):
        ip = self.phone_ip.text().strip()
        port = self.phone_port.text().strip() or "4242"
        if not ip:
            return

        try:
            text = self.config_path.read_text() if self.config_path.exists() else ""
            if f"target_host = {ip}" in text:
                QMessageBox.information(self, "Already exists", f"TCP client to {ip} already in config.")
                return

            entry = f"\n[[TCP Client {ip}]]\n  type = TCPClientInterface\n  interface_enabled = Yes\n  target_host = {ip}\n  target_port = {port}\n"
            self.config_path.write_text(text.rstrip() + "\n" + entry)
            QMessageBox.information(self, "Added", f"TCP client to {ip}:{port} added.\nRestart app to apply.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _open_config_editor(self):
        dialog = ConfigEditorDialog(self.config_path, self)
        dialog.exec()

    def _restart_app(self):
        if QMessageBox.question(self, "Restart", "Restart the application now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            import os, sys
            from PyQt6.QtWidgets import QApplication
            try:
                os.execv(sys.executable, [sys.executable, "-m", "src.main"])
            except:
                QApplication.quit()
