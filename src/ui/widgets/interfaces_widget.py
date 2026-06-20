"""Interfaces tab — manage RNS interfaces from the app."""

import RNS
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QGroupBox, QMessageBox, QLineEdit, QDialog, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QComboBox,
    QApplication, QMenu
)
from PyQt6.QtCore import Qt, QTimer
from src.config.theme import MeshTheme
from src.ui.widgets.common import StatusDot


class ConfigEditorDialog(QDialog):
    def __init__(self, config_path, parent=None):
        super().__init__(parent)
        self.config_path = config_path
        self.setWindowTitle("Reticulum Config Editor")
        self.setMinimumSize(700, 500)
        self.setStyleSheet(f"background-color: {MeshTheme.CANVAS};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel("Config Editor")
        header.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {MeshTheme.TEXT}; background: transparent;")
        layout.addWidget(header)

        warning = QLabel("Editing this file directly can break RNS. Restart app after saving.")
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

        reload_btn = QPushButton("Reload")
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
        return self.config_path.read_text() if self.config_path.exists() else ""

    def _reload(self):
        self.editor.setPlainText(self._load())

    def _save(self):
        try:
            self.config_path.write_text(self.editor.toPlainText())
            QMessageBox.information(self, "Saved", "Config saved. Restart app to apply.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


def _parse_config_interfaces(config_path):
    """Parse RNS config file and return list of interface dicts."""
    ifaces = []
    if not config_path.exists():
        return ifaces

    text = config_path.read_text()
    lines = text.splitlines()

    current = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[[") and stripped.endswith("]]"):
            sec_name = stripped[2:-2].strip()
            if current:
                ifaces.append(current)
            current = {"section": sec_name, "name": sec_name, "type": "", "enabled": "Yes",
                       "port": "", "speed": "", "listen_ip": "", "listen_port": "",
                       "target_host": "", "target_port": "", "raw": stripped}
        elif current is not None:
            if stripped.startswith("[[") and stripped.endswith("]]"):
                pass
            if "=" in stripped and not stripped.startswith("#"):
                key, val = stripped.split("=", 1)
                key = key.strip()
                val = val.strip()
                if key == "type":
                    current["type"] = val
                elif key == "interface_enabled":
                    current["enabled"] = val
                elif key == "port":
                    current["port"] = val
                elif key == "speed":
                    current["speed"] = val
                elif key == "listen_ip":
                    current["listen_ip"] = val
                elif key == "listen_port":
                    current["listen_port"] = val
                elif key == "target_host":
                    current["target_host"] = val
                    current["name"] = f"TCP Client {val}"
                elif key == "target_port":
                    current["target_port"] = val
        elif stripped.startswith("[[") and stripped.endswith("]]"):
            pass

    if current:
        ifaces.append(current)

    return ifaces


def _remove_config_section(config_path, section_name):
    """Remove a [[section]] from the RNS config file."""
    if not config_path.exists():
        return
    text = config_path.read_text()
    lines = text.splitlines()
    output = []
    skip = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[[") and stripped.endswith("]]"):
            sec = stripped[2:-2].strip()
            if sec == section_name:
                skip = True
            else:
                skip = False
        if not skip:
            output.append(line)
    config_path.write_text("\n".join(output) + "\n")


class InterfacesWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.rns_node = getattr(backend, 'rns_node', None)
        self.config_path = Path.home() / ".reticulum" / "config"
        self.init_ui()
        self._refresh_status()

    def init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
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

        # === Active Interfaces (from RNS runtime) ===
        active_group = QGroupBox("Active Interfaces")
        active_group.setStyleSheet(group_style())
        active_layout = QVBoxLayout()

        self.active_table = QTableWidget()
        self.active_table.setColumnCount(5)
        self.active_table.setHorizontalHeaderLabels(["Name", "Type", "Status", "RX", "TX"])
        self.active_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.active_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.active_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.active_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.active_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.active_table.setStyleSheet(f"""
            QTableWidget {{ background: transparent; border: 1px solid {MeshTheme.BORDER_CARD}; border-radius: 12px; }}
            QTableWidget::item {{ color: {MeshTheme.TEXT}; padding: 6px 8px; }}
            QHeaderView::section {{ background: {MeshTheme.SURFACE}; color: {MeshTheme.TEXT_MUTED};
                border: none; border-bottom: 1px solid {MeshTheme.BORDER}; padding: 6px 8px; font-weight: 600; font-size: 12px; }}
        """)
        active_layout.addWidget(self.active_table)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {MeshTheme.ACTION_PRIMARY}; color: white; border: none;
                border-radius: 12px; padding: 8px 20px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background-color: {MeshTheme.ACTION_PRIMARY_HOVER}; }}
        """)
        refresh_btn.clicked.connect(self._refresh_status)
        active_layout.addWidget(refresh_btn)

        active_group.setLayout(active_layout)
        layout.addWidget(active_group)

        # === Configured Interfaces (from config file) ===
        config_group = QGroupBox("Configured Interfaces")
        config_group.setStyleSheet(group_style())
        config_layout = QVBoxLayout()

        config_desc = QLabel("These are the interfaces in your RNS config file. Add or remove them here — no need to edit the config file manually.")
        config_desc.setWordWrap(True)
        config_desc.setStyleSheet(f"color: {MeshTheme.TEXT_MUTED}; font-size: 12px; background: transparent;")
        config_layout.addWidget(config_desc)

        self.config_table = QTableWidget()
        self.config_table.setColumnCount(4)
        self.config_table.setHorizontalHeaderLabels(["Name", "Type", "Enabled", "Details"])
        self.config_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.config_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.config_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.config_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.config_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.config_table.customContextMenuRequested.connect(self._config_context_menu)
        self.config_table.setStyleSheet(f"""
            QTableWidget {{ background: transparent; border: 1px solid {MeshTheme.BORDER_CARD}; border-radius: 12px; }}
            QTableWidget::item {{ color: {MeshTheme.TEXT}; padding: 6px 8px; }}
            QTableWidget::item:selected {{ background: {MeshTheme.ACTION_PRIMARY}; color: white; }}
            QHeaderView::section {{ background: {MeshTheme.SURFACE}; color: {MeshTheme.TEXT_MUTED};
                border: none; border-bottom: 1px solid {MeshTheme.BORDER}; padding: 6px 8px; font-weight: 600; font-size: 12px; }}
        """)
        config_layout.addWidget(self.config_table)

        config_btn_row = QHBoxLayout()

        reload_cfg_btn = QPushButton("Reload List")
        reload_cfg_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {MeshTheme.TEXT_MUTED};
                border: 1px solid {MeshTheme.BORDER}; border-radius: 12px; padding: 8px 16px; font-size: 12px; }}
            QPushButton:hover {{ background-color: {MeshTheme.SURFACE_VARIANT}; color: {MeshTheme.TEXT}; }}
        """)
        reload_cfg_btn.clicked.connect(self._refresh_config_table)
        config_btn_row.addWidget(reload_cfg_btn)

        config_btn_row.addStretch()

        config_layout.addLayout(config_btn_row)
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # === Add Interface ===
        add_group = QGroupBox("Add Interface")
        add_group.setStyleSheet(group_style())
        add_layout = QVBoxLayout()

        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Type:"))
        self.iface_type = QComboBox()
        self.iface_type.addItem("TCP Server", "TCPServerInterface")
        self.iface_type.addItem("TCP Client", "TCPClientInterface")
        self.iface_type.addItem("Serial", "SerialInterface")
        self.iface_type.addItem("KISS (TNC)", "KISSInterface")
        self.iface_type.addItem("Auto (Local Network)", "AutoInterface")
        self.iface_type.setStyleSheet(f"""
            QComboBox {{ background-color: {MeshTheme.INPUT_BG}; color: {MeshTheme.TEXT};
                border: 1px solid {MeshTheme.INPUT_BORDER}; border-radius: 12px; padding: 8px 14px; font-size: 13px; }}
            QComboBox::drop-down {{ border: none; }}
        """)
        self.iface_type.currentIndexChanged.connect(self._on_type_changed)
        type_row.addWidget(self.iface_type)
        add_layout.addLayout(type_row)

        # TCP Server fields
        self.server_fields = QWidget()
        sf_layout = QHBoxLayout(self.server_fields)
        sf_layout.setContentsMargins(0, 0, 0, 0)
        sf_layout.addWidget(QLabel("Listen IP:"))
        self.server_ip = QLineEdit("0.0.0.0")
        self.server_ip.setMaximumWidth(120)
        self.server_ip.setStyleSheet(f"background-color: {MeshTheme.INPUT_BG}; color: {MeshTheme.TEXT}; border: 1px solid {MeshTheme.INPUT_BORDER}; border-radius: 8px; padding: 6px 10px; font-size: 13px;")
        sf_layout.addWidget(self.server_ip)
        sf_layout.addWidget(QLabel("Port:"))
        self.server_port = QLineEdit("4242")
        self.server_port.setMaximumWidth(70)
        self.server_port.setStyleSheet(f"background-color: {MeshTheme.INPUT_BG}; color: {MeshTheme.TEXT}; border: 1px solid {MeshTheme.INPUT_BORDER}; border-radius: 8px; padding: 6px 10px; font-size: 13px;")
        sf_layout.addWidget(self.server_port)
        add_layout.addWidget(self.server_fields)

        # TCP Client fields
        self.client_fields = QWidget()
        cf_layout = QHBoxLayout(self.client_fields)
        cf_layout.setContentsMargins(0, 0, 0, 0)
        cf_layout.addWidget(QLabel("Host:"))
        self.client_host = QLineEdit()
        self.client_host.setPlaceholderText("10.10.100.12")
        self.client_host.setMaximumWidth(140)
        self.client_host.setStyleSheet(f"background-color: {MeshTheme.INPUT_BG}; color: {MeshTheme.TEXT}; border: 1px solid {MeshTheme.INPUT_BORDER}; border-radius: 8px; padding: 6px 10px; font-size: 13px;")
        cf_layout.addWidget(self.client_host)
        cf_layout.addWidget(QLabel("Port:"))
        self.client_port = QLineEdit("4242")
        self.client_port.setMaximumWidth(70)
        self.client_port.setStyleSheet(f"background-color: {MeshTheme.INPUT_BG}; color: {MeshTheme.TEXT}; border: 1px solid {MeshTheme.INPUT_BORDER}; border-radius: 8px; padding: 6px 10px; font-size: 13px;")
        cf_layout.addWidget(self.client_port)
        add_layout.addWidget(self.client_fields)

        # Serial fields
        self.serial_fields = QWidget()
        ser_layout = QHBoxLayout(self.serial_fields)
        ser_layout.setContentsMargins(0, 0, 0, 0)
        ser_layout.addWidget(QLabel("Port:"))
        self.serial_port = QLineEdit("/dev/ttyUSB0")
        self.serial_port.setMaximumWidth(140)
        self.serial_port.setStyleSheet(f"background-color: {MeshTheme.INPUT_BG}; color: {MeshTheme.TEXT}; border: 1px solid {MeshTheme.INPUT_BORDER}; border-radius: 8px; padding: 6px 10px; font-size: 13px;")
        ser_layout.addWidget(self.serial_port)
        ser_layout.addWidget(QLabel("Baud:"))
        self.serial_baud = QLineEdit("115200")
        self.serial_baud.setMaximumWidth(80)
        self.serial_baud.setStyleSheet(f"background-color: {MeshTheme.INPUT_BG}; color: {MeshTheme.TEXT}; border: 1px solid {MeshTheme.INPUT_BORDER}; border-radius: 8px; padding: 6px 10px; font-size: 13px;")
        ser_layout.addWidget(self.serial_baud)
        self.serial_flow = QCheckBox("Flow Control")
        self.serial_flow.setStyleSheet(f"color: {MeshTheme.TEXT}; background: transparent;")
        ser_layout.addWidget(self.serial_flow)
        add_layout.addWidget(self.serial_fields)

        # Auto fields (none needed)
        self.auto_fields = QLabel("AutoInterface discovers other RNS nodes on your local network automatically. No configuration needed.")
        self.auto_fields.setWordWrap(True)
        self.auto_fields.setStyleSheet(f"color: {MeshTheme.TEXT_MUTED}; font-size: 12px; background: transparent;")
        add_layout.addWidget(self.auto_fields)

        add_btn = QPushButton("Add Interface")
        add_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {MeshTheme.ACTION_PRIMARY}; color: white; border: none;
                border-radius: 12px; padding: 10px 24px; font-size: 14px; font-weight: 600; }}
            QPushButton:hover {{ background-color: {MeshTheme.ACTION_PRIMARY_HOVER}; }}
        """)
        add_btn.clicked.connect(self._add_interface)
        add_layout.addWidget(add_btn)

        add_group.setLayout(add_layout)
        layout.addWidget(add_group)

        # === Config Editor + Restart ===
        tools_group = QGroupBox("Tools")
        tools_group.setStyleSheet(group_style())
        tools_layout = QHBoxLayout()

        editor_btn = QPushButton("Config Editor")
        editor_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {MeshTheme.ACCENT};
                border: 1px solid {MeshTheme.ACCENT}; border-radius: 12px; padding: 10px 20px; font-size: 13px; }}
            QPushButton:hover {{ background-color: {MeshTheme.ACCENT}20; }}
        """)
        editor_btn.clicked.connect(self._open_config_editor)
        tools_layout.addWidget(editor_btn)

        restart_rns_btn = QPushButton("Restart RNS")
        restart_rns_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {MeshTheme.SURFACE_LIGHT}; color: {MeshTheme.TEXT};
                border: none; border-radius: 12px; padding: 10px 20px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background-color: {MeshTheme.BORDER_STRONG}; }}
        """)
        restart_rns_btn.clicked.connect(self._restart_rns)
        tools_layout.addWidget(restart_rns_btn)

        restart_app_btn = QPushButton("Restart App")
        restart_app_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {MeshTheme.WARNING}; color: white; border: none;
                border-radius: 12px; padding: 10px 20px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background-color: #f97316; }}
        """)
        restart_app_btn.clicked.connect(self._restart_app)
        tools_layout.addWidget(restart_app_btn)

        tools_group.setLayout(tools_layout)
        layout.addWidget(tools_group)

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        self._on_type_changed(0)
        self._refresh_config_table()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_status)
        self._timer.start(5000)

    def _on_type_changed(self, idx):
        iface_type = self.iface_type.currentData()
        self.server_fields.setVisible(iface_type == "TCPServerInterface")
        self.client_fields.setVisible(iface_type == "TCPClientInterface")
        self.serial_fields.setVisible(iface_type in ("SerialInterface", "KISSInterface"))
        self.auto_fields.setVisible(iface_type == "AutoInterface")

    def _refresh_status(self):
        ifaces = []
        try:
            for iface in RNS.Transport.interfaces:
                name = str(getattr(iface, "name", str(iface)))
                ifaces.append({
                    "name": name,
                    "type": type(iface).__name__,
                    "online": getattr(iface, "online", False),
                    "bytes_in": getattr(iface, "bytes_in", 0),
                    "bytes_out": getattr(iface, "bytes_out", 0),
                })
        except:
            pass

        self.active_table.setRowCount(len(ifaces))
        for i, iface in enumerate(ifaces):
            self.active_table.setItem(i, 0, QTableWidgetItem(iface["name"]))
            self.active_table.setItem(i, 1, QTableWidgetItem(iface["type"]))
            status = "Online" if iface["online"] else "Offline"
            item = QTableWidgetItem(status)
            if iface["online"]:
                item.setForeground(Qt.GlobalColor.green)
            else:
                item.setForeground(Qt.GlobalColor.gray)
            self.active_table.setItem(i, 2, item)
            self.active_table.setItem(i, 3, QTableWidgetItem(self._fmt_bytes(iface["bytes_in"])))
            self.active_table.setItem(i, 4, QTableWidgetItem(self._fmt_bytes(iface["bytes_out"])))

    def _refresh_config_table(self):
        ifaces = _parse_config_interfaces(self.config_path)
        self.config_table.setRowCount(len(ifaces))
        for i, iface in enumerate(ifaces):
            self.config_table.setItem(i, 0, QTableWidgetItem(iface.get("name", "")))
            self.config_table.setItem(i, 1, QTableWidgetItem(iface.get("type", "")))
            self.config_table.setItem(i, 2, QTableWidgetItem(iface.get("enabled", "")))

            details = ""
            if iface.get("listen_port"):
                details = f"Listen {iface.get('listen_ip', '')}:{iface['listen_port']}"
            elif iface.get("target_host"):
                details = f"Connect {iface['target_host']}:{iface.get('target_port', '')}"
            elif iface.get("port"):
                details = f"{iface['port']} @ {iface.get('speed', '')} baud"
            elif iface.get("type") == "AutoInterface":
                details = "Auto-discovery"
            self.config_table.setItem(i, 3, QTableWidgetItem(details))

    def _config_context_menu(self, pos):
        item = self.config_table.itemAt(pos)
        if not item:
            return
        row = item.row()
        section_name = self.config_table.item(row, 0).text()

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background-color: {MeshTheme.SURFACE}; border: 1px solid {MeshTheme.BORDER}; border-radius: 12px; padding: 4px; }}
            QMenu::item {{ padding: 8px 24px; border-radius: 8px; color: {MeshTheme.TEXT}; }}
            QMenu::item:selected {{ background-color: {MeshTheme.ERROR}; color: white; }}
        """)
        delete_a = menu.addAction("Delete Interface")
        action = menu.exec(self.config_table.viewport().mapToGlobal(pos))
        if action == delete_a:
            reply = QMessageBox.question(self, "Delete", f"Delete interface '{section_name}'?\nRestart app to apply.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                _remove_config_section(self.config_path, section_name)
                self._refresh_config_table()

    def _add_interface(self):
        iface_type = self.iface_type.currentData()
        try:
            text = self.config_path.read_text() if self.config_path.exists() else ""
            entry = ""
            section_name = ""

            if iface_type == "TCPServerInterface":
                ip = self.server_ip.text().strip() or "0.0.0.0"
                port = self.server_port.text().strip() or "4242"
                section_name = f"TCP Server {port}"
                entry = f"\n[[{section_name}]]\n  type = TCPServerInterface\n  interface_enabled = Yes\n  listen_ip = {ip}\n  listen_port = {port}\n"

            elif iface_type == "TCPClientInterface":
                host = self.client_host.text().strip()
                port = self.client_port.text().strip() or "4242"
                if not host:
                    QMessageBox.warning(self, "Error", "Enter a host IP.")
                    return
                section_name = f"TCP Client {host}"
                entry = f"\n[[{section_name}]]\n  type = TCPClientInterface\n  interface_enabled = Yes\n  target_host = {host}\n  target_port = {port}\n"

            elif iface_type == "SerialInterface":
                port = self.serial_port.text().strip() or "/dev/ttyUSB0"
                baud = self.serial_baud.text().strip() or "115200"
                section_name = f"Serial {port}"
                entry = f"\n[[{section_name}]]\n  type = SerialInterface\n  interface_enabled = Yes\n  port = {port}\n  speed = {baud}\n"
                if self.serial_flow.isChecked():
                    entry += "  flow_control = Yes\n"

            elif iface_type == "KISSInterface":
                port = self.serial_port.text().strip() or "/dev/ttyUSB0"
                baud = self.serial_baud.text().strip() or "115200"
                section_name = f"KISS {port}"
                entry = f"\n[[{section_name}]]\n  type = KISSInterface\n  interface_enabled = Yes\n  port = {port}\n  speed = {baud}\n  preamble = AA\n  txtail = 0\n  persistence = 200\n  slottime = 20\n"

            elif iface_type == "AutoInterface":
                section_name = "AutoInterface"
                if "AutoInterface" in text:
                    QMessageBox.information(self, "Exists", "AutoInterface already in config.")
                    return
                entry = "\n[[AutoInterface]]\n  type = AutoInterface\n  interface_enabled = Yes\n"

            if entry:
                self.config_path.write_text(text.rstrip() + "\n" + entry)
                self._refresh_config_table()
                QMessageBox.information(self, "Added", f"{iface_type} added to config.\nRestart app to apply.")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _open_config_editor(self):
        dialog = ConfigEditorDialog(self.config_path, self)
        dialog.exec()
        self._refresh_config_table()

    def _restart_app(self):
        reply = QMessageBox.question(self, "Restart", "Restart the application now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        import os, sys, subprocess
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        app.quit()

        # Use subprocess to start a new process instead of execv
        # This is more reliable across different environments
        cwd = os.getcwd()
        python = sys.executable

        # Try different launch methods
        try:
            subprocess.Popen([python, "-m", "src.main"], cwd=cwd, start_new_session=True)
        except:
            try:
                subprocess.Popen([python, "src/main.py"], cwd=cwd, start_new_session=True)
            except:
                try:
                    # Last resort: just restart with the same command
                    subprocess.Popen(sys.argv, cwd=cwd, start_new_session=True)
                except:
                    pass

    def _restart_rns(self):
        reply = QMessageBox.question(self, "Restart RNS",
            "Restart Reticulum without closing the app?\nThis re-reads the config file.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            import threading
            if self.rns_node:
                def do_restart():
                    try:
                        self.rns_node.reticulum = RNS.Reticulum(configdir=str(self.rns_node.rns_config_dir))
                        self.rns_node.identity = self.rns_node._load_or_create_identity()
                        if self.backend and hasattr(self.backend, 'lxmf_messenger') and self.backend.lxmf_messenger:
                            display_name = self.backend.get_display_name() if hasattr(self.backend, 'get_display_name') else ""
                            self.backend.lxmf_messenger.announce(display_name)
                    except Exception as e:
                        print(f"[RNS] Restart error: {e}")

                t = threading.Thread(target=do_restart, daemon=True)
                t.start()

                QTimer.singleShot(3000, self._refresh_status)
                QTimer.singleShot(3000, self._refresh_config_table)
                QMessageBox.information(self, "Restarted", "RNS reinitialized. Refreshing...")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not restart RNS: {e}")

    def _fmt_bytes(self, b):
        if b < 1024:
            return f"{b} B"
        elif b < 1024 * 1024:
            return f"{b/1024:.1f} KB"
        else:
            return f"{b/(1024*1024):.1f} MB"
