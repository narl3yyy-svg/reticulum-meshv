"""Settings widget with identity hash display and announce button."""

import RNS
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFileDialog, QCheckBox, QGroupBox, QMessageBox, QTextEdit, QApplication,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from pathlib import Path
import sys
import os
import configparser
from src.config.theme import MeshTheme


class SettingsWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.rns_node = getattr(backend, 'rns_node', None)
        self.serial_interfaces = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        scroll = QWidget()
        scroll_layout = QVBoxLayout(scroll)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(16)

        title = QLabel("Settings")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {MeshTheme.TEXT}; background: transparent;")
        scroll_layout.addWidget(title)

        def group_style():
            return f"""
                QGroupBox {{ color: {MeshTheme.TEXT_MUTED}; font-size: 12px;
                    border: 1px solid {MeshTheme.BORDER}; border-radius: 10px; margin-top: 20px;
                    padding: 16px; }}
                QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left;
                    padding: 4px 12px; color: {MeshTheme.TEXT_MUTED}; font-size: 12px; }}
            """

        # === Identity Section ===
        id_group = QGroupBox("Your Identity")
        id_group.setStyleSheet(group_style())
        id_layout = QVBoxLayout()

        self.identity_label = QLabel()
        self.identity_label.setStyleSheet(f"font-family: 'JetBrains Mono', monospace; background: {MeshTheme.SURFACE_VARIANT}; padding: 10px; border-radius: 8px; font-size: 12px; color: {MeshTheme.TEXT};")
        self._update_identity_display()
        id_layout.addWidget(self.identity_label)

        announce_btn = QPushButton("Announce Myself on Network")
        announce_btn.clicked.connect(self._announce_myself)
        id_layout.addWidget(announce_btn)

        note = QLabel("Announcing makes you visible to other nodes on the Reticulum network.")
        note.setStyleSheet(f"color: {MeshTheme.TEXT_DIM}; font-size: 11px; background: transparent;")
        id_layout.addWidget(note)

        id_group.setLayout(id_layout)
        scroll_layout.addWidget(id_group)

        # === Downloads ===
        dl_group = QGroupBox("File Downloads")
        dl_group.setStyleSheet(group_style())
        dl_layout = QVBoxLayout()

        self.download_path = QLineEdit()
        self.download_path.setReadOnly(True)
        if hasattr(self.backend, 'downloads_dir'):
            self.download_path.setText(str(self.backend.downloads_dir))

        browse_btn = QPushButton("Change Download Folder...")
        browse_btn.clicked.connect(self._change_download_folder)

        label = QLabel("Received files & extracted folders are saved to:")
        label.setStyleSheet(f"color: {MeshTheme.TEXT}; background: transparent;")
        dl_layout.addWidget(label)
        dl_layout.addWidget(self.download_path)
        dl_layout.addWidget(browse_btn)
        dl_group.setLayout(dl_layout)
        scroll_layout.addWidget(dl_group)

        # === Network Interfaces ===
        iface_group = QGroupBox("Network Interfaces")
        iface_group.setStyleSheet(group_style())
        iface_layout = QVBoxLayout()

        self.config_path_label = QLabel(f"Config: {Path.home() / '.reticulum' / 'config'}")
        self.config_path_label.setStyleSheet(f"font-family: 'JetBrains Mono', monospace; font-size: 11px; color: {MeshTheme.TEXT_DIM}; background: transparent;")
        iface_layout.addWidget(self.config_path_label)

        self.auto_interface_cb = QCheckBox("AutoInterface enabled")
        self.auto_interface_cb.setStyleSheet(f"color: {MeshTheme.TEXT}; background: transparent;")
        self.auto_interface_cb.setChecked(True)
        iface_layout.addWidget(self.auto_interface_cb)

        tcp_layout = QHBoxLayout()
        self.tcp_server_cb = QCheckBox("TCPServer on port:")
        self.tcp_server_cb.setStyleSheet(f"color: {MeshTheme.TEXT}; background: transparent;")
        self.tcp_port = QLineEdit("4242")
        self.tcp_port.setMaximumWidth(80)
        tcp_layout.addWidget(self.tcp_server_cb)
        tcp_layout.addWidget(self.tcp_port)
        tcp_layout.addStretch()
        iface_layout.addLayout(tcp_layout)

        save_iface_btn = QPushButton("Save Network Settings")
        save_iface_btn.clicked.connect(self._save_interface_settings)
        iface_layout.addWidget(save_iface_btn)

        iface_group.setLayout(iface_layout)
        scroll_layout.addWidget(iface_group)

        # === Serial Interfaces ===
        serial_group = QGroupBox("Serial / Radio Interfaces")
        serial_group.setStyleSheet(group_style())
        serial_layout = QVBoxLayout()

        serial_desc = QLabel(
            "Configure serial interfaces for LoRa radios, TNCs, and other serial devices.\n"
            "Supports SerialInterface (direct) and KISSInterface (TNC protocol)."
        )
        serial_desc.setStyleSheet(f"color: {MeshTheme.TEXT_MUTED}; font-size: 11px; background: transparent;")
        serial_desc.setWordWrap(True)
        serial_layout.addWidget(serial_desc)

        self.serial_table = QTableWidget()
        self.serial_table.setColumnCount(4)
        self.serial_table.setHorizontalHeaderLabels(["Type", "Port", "Baud Rate", "Flow Control"])
        self.serial_table.horizontalHeader().setStretchLastSection(False)
        self.serial_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.serial_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.serial_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.serial_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.serial_table.setMaximumHeight(160)
        self.serial_table.setAlternatingRowColors(True)
        self.serial_table.setStyleSheet(f"""
            QTableWidget {{ background: transparent; border: 1px solid {MeshTheme.BORDER}; border-radius: 8px; }}
            QTableWidget::item {{ color: {MeshTheme.TEXT}; padding: 4px 8px; font-size: 12px; }}
            QTableWidget::item:selected {{ background: {MeshTheme.ACCENT}; color: white; }}
            QHeaderView::section {{ background: {MeshTheme.SURFACE}; color: {MeshTheme.TEXT_MUTED};
                border: none; border-bottom: 1px solid {MeshTheme.BORDER}; padding: 4px 8px; font-weight: 600; font-size: 11px; }}
        """)
        serial_layout.addWidget(self.serial_table)

        serial_btn_row = QHBoxLayout()
        add_serial_btn = QPushButton("+ Add Serial Interface")
        add_serial_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {MeshTheme.ACCENT};
                border: 1px solid {MeshTheme.ACCENT}; border-radius: 6px;
                padding: 4px 12px; font-size: 11px; }}
            QPushButton:hover {{ background-color: {MeshTheme.ACCENT}20; }}
        """)
        add_serial_btn.clicked.connect(self._add_serial_interface)
        serial_btn_row.addWidget(add_serial_btn)

        add_kiss_btn = QPushButton("+ Add KISS Interface")
        add_kiss_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {MeshTheme.SUCCESS};
                border: 1px solid {MeshTheme.SUCCESS}; border-radius: 6px;
                padding: 4px 12px; font-size: 11px; }}
            QPushButton:hover {{ background-color: {MeshTheme.SUCCESS}20; }}
        """)
        add_kiss_btn.clicked.connect(lambda: self._add_serial_interface(kiss=True))
        serial_btn_row.addWidget(add_kiss_btn)

        remove_serial_btn = QPushButton("Remove Selected")
        remove_serial_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {MeshTheme.ERROR};
                border: 1px solid {MeshTheme.ERROR}; border-radius: 6px;
                padding: 4px 12px; font-size: 11px; }}
            QPushButton:hover {{ background-color: {MeshTheme.ERROR}20; }}
        """)
        remove_serial_btn.clicked.connect(self._remove_serial_interface)
        serial_btn_row.addWidget(remove_serial_btn)

        serial_btn_row.addStretch()
        serial_layout.addLayout(serial_btn_row)

        save_serial_btn = QPushButton("Save Serial Settings")
        save_serial_btn.clicked.connect(self._save_serial_interfaces)
        serial_layout.addWidget(save_serial_btn)

        serial_group.setLayout(serial_layout)
        scroll_layout.addWidget(serial_group)

        # === Message Privacy ===
        msg_group = QGroupBox("Message Privacy")
        msg_group.setStyleSheet(group_style())
        msg_layout = QVBoxLayout()

        msg_label = QLabel("Who can send you messages:")
        msg_label.setStyleSheet(f"color: {MeshTheme.TEXT}; background: transparent;")
        msg_layout.addWidget(msg_label)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("Allow all", "all")
        self.filter_combo.addItem("Trusted contacts only", "trusted")
        self.filter_combo.addItem("Block all unknown", "blocked")
        self.filter_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {MeshTheme.INPUT_BG}; color: {MeshTheme.TEXT};
                border: 1px solid {MeshTheme.INPUT_BORDER}; border-radius: 8px;
                padding: 8px 12px; font-size: 13px;
            }}
            QComboBox::drop-down {{
                border: none; padding-right: 8px;
            }}
            QComboBox::item:selected {{
                background-color: {MeshTheme.ACCENT}; color: white;
            }}
        """)
        current_filter = self.backend.get_message_filter() if hasattr(self.backend, 'get_message_filter') else "all"
        idx = self.filter_combo.findData(current_filter)
        if idx >= 0:
            self.filter_combo.setCurrentIndex(idx)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        msg_layout.addWidget(self.filter_combo)

        filter_note = QLabel(
            "Trusted contacts can be managed from the Contacts tab.\n"
            "Blocked senders are silently ignored."
        )
        filter_note.setStyleSheet(f"color: {MeshTheme.TEXT_DIM}; font-size: 11px; background: transparent;")
        filter_note.setWordWrap(True)
        msg_layout.addWidget(filter_note)

        msg_group.setLayout(msg_layout)
        scroll_layout.addWidget(msg_group)

        restart_btn = QPushButton("Restart Application Now")
        restart_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {MeshTheme.WARNING}; color: white; border: none;
                border-radius: 8px; padding: 10px 20px; font-size: 14px; font-weight: 600; }}
            QPushButton:hover {{ background-color: #f97316; }}
        """)
        restart_btn.clicked.connect(self._restart_application)
        scroll_layout.addWidget(restart_btn)

        scroll_layout.addStretch()

        from PyQt6.QtWidgets import QScrollArea
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setWidget(scroll)
        layout.addWidget(sa)

        self._load_current_interface_settings()
        self._load_serial_interfaces()

    def _update_identity_display(self):
        if self.rns_node and self.rns_node.identity:
            try:
                full_hash = self.rns_node.get_identity_hash()
                text = f"Your Identity Hash:\n{full_hash}"
                self.identity_label.setText(text)
            except:
                self.identity_label.setText("Could not load identity hash.")
        else:
            self.identity_label.setText("Identity not loaded.")

    def _announce_myself(self):
        if self.rns_node and self.rns_node.announce_myself():
            QMessageBox.information(self, "Announced", "You are now visible on the Reticulum network.")
        else:
            QMessageBox.warning(self, "Error", "Could not announce (Reticulum not ready).")

    def _save_interface_settings(self):
        config_path = Path.home() / ".reticulum" / "config"
        text = config_path.read_text() if config_path.exists() else ""

        lines = text.splitlines()
        new_lines = []
        in_auto = False
        in_tcp = False
        auto_done = False
        tcp_done = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("[[") and stripped.endswith("]]"):
                sec_name = stripped[2:-2].strip()
                in_auto = sec_name == "AutoInterface" or "AutoInterface" in sec_name
                in_tcp = "TCPServerInterface" in sec_name
                if in_auto:
                    auto_done = True
                if in_tcp:
                    tcp_done = True
            if in_auto and stripped.startswith("interface_enabled"):
                line = f"  interface_enabled = {'Yes' if self.auto_interface_cb.isChecked() else 'No'}"
            if in_tcp and stripped.startswith("interface_enabled"):
                line = f"  interface_enabled = {'Yes' if self.tcp_server_cb.isChecked() else 'No'}"
            if in_tcp and stripped.startswith("listen_port"):
                line = f"  listen_port = {self.tcp_port.text().strip()}"
            new_lines.append(line)

        if not auto_done:
            new_lines.append("")
            new_lines.append("[[AutoInterface]]")
            new_lines.append(f"  interface_enabled = {'Yes' if self.auto_interface_cb.isChecked() else 'No'}")
        if not tcp_done:
            new_lines.append("")
            new_lines.append("[[TCPServerInterface]]")
            new_lines.append(f"  interface_enabled = {'Yes' if self.tcp_server_cb.isChecked() else 'No'}")
            new_lines.append(f"  listen_port = {self.tcp_port.text().strip()}")

        try:
            config_path.write_text("\n".join(new_lines) + "\n")
            QMessageBox.information(self, "Saved", "Interface settings saved. Restart to apply.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _load_current_interface_settings(self):
        config_path = Path.home() / ".reticulum" / "config"
        if not config_path.exists():
            return
        try:
            text = config_path.read_text()
            lines = text.splitlines()
            in_auto = False
            in_tcp = False
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("[[") and stripped.endswith("]]"):
                    sec_name = stripped[2:-2].strip()
                    in_auto = "AutoInterface" in sec_name
                    in_tcp = "TCPServerInterface" in sec_name
                    continue
                if in_auto and stripped.startswith("interface_enabled"):
                    self.auto_interface_cb.setChecked(stripped.split("=", 1)[1].strip().lower() in ("yes", "true"))
                if in_tcp and stripped.startswith("interface_enabled"):
                    self.tcp_server_cb.setChecked(stripped.split("=", 1)[1].strip().lower() in ("yes", "true"))
                if in_tcp and stripped.startswith("listen_port"):
                    self.tcp_port.setText(stripped.split("=", 1)[1].strip())
        except:
            pass

    def _change_download_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose download folder")
        if folder:
            self.download_path.setText(folder)
            if hasattr(self.backend, 'downloads_dir'):
                self.backend.downloads_dir = Path(folder)

    def _on_filter_changed(self, idx):
        mode = self.filter_combo.itemData(idx)
        if hasattr(self.backend, 'set_message_filter'):
            self.backend.set_message_filter(mode)
        sb = self._find_status_bar()
        if sb:
            sb.showMessage(f"Message filter set to: {mode}", 3000)

    def _find_status_bar(self):
        p = self.parent()
        while p:
            if hasattr(p, 'statusBar'):
                return p.statusBar()
            p = p.parent()
        return None

    def _add_serial_interface(self, kiss=False):
        iface_type = "KISSInterface" if kiss else "SerialInterface"
        self.serial_interfaces.append({
            "type": iface_type,
            "port": "/dev/ttyUSB0",
            "speed": "115200",
            "flow_control": "0",
        })
        self._refresh_serial_table()

    def _remove_serial_interface(self):
        row = self.serial_table.currentRow()
        if row < 0 or row >= len(self.serial_interfaces):
            return
        del self.serial_interfaces[row]
        self._refresh_serial_table()

    def _refresh_serial_table(self):
        self.serial_table.setRowCount(len(self.serial_interfaces))
        for i, sif in enumerate(self.serial_interfaces):
            self.serial_table.setItem(i, 0, QTableWidgetItem(sif["type"]))
            self.serial_table.setItem(i, 1, QTableWidgetItem(sif["port"]))
            self.serial_table.setItem(i, 2, QTableWidgetItem(str(sif["speed"])))
            self.serial_table.setItem(i, 3, QTableWidgetItem(str(sif.get("flow_control", "0"))))
        self.serial_table.resizeColumnsToContents()

    def _save_serial_interfaces(self):
        for i in range(self.serial_table.rowCount()):
            if i >= len(self.serial_interfaces):
                break
            self.serial_interfaces[i]["port"] = self.serial_table.item(i, 1).text() if self.serial_table.item(i, 1) else "/dev/ttyUSB0"
            self.serial_interfaces[i]["speed"] = self.serial_table.item(i, 2).text() if self.serial_table.item(i, 2) else "115200"
            self.serial_interfaces[i]["flow_control"] = self.serial_table.item(i, 3).text() if self.serial_table.item(i, 3) else "0"

        config_path = Path.home() / ".reticulum" / "config"
        text = config_path.read_text() if config_path.exists() else ""
        lines = text.splitlines()
        kept = []
        skip = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("[[") and stripped.endswith("]]"):
                sec_name = stripped[2:-2].strip()
                skip = "Serial" in sec_name or "KISS" in sec_name
            if skip and stripped.startswith("[[") and stripped.endswith("]]") and not ("Serial" in stripped or "KISS" in stripped):
                skip = False
            if not skip:
                kept.append(line)

        for i, sif in enumerate(self.serial_interfaces):
            kept.append("")
            kept.append(f"[[Serial{i+1}_{sif['type']}]]")
            kept.append(f"  type = {sif['type']}")
            kept.append("  interface_enabled = Yes")
            kept.append(f"  port = {sif['port']}")
            kept.append(f"  speed = {sif['speed']}")
            if sif["type"] == "SerialInterface" and sif.get("flow_control", "0") != "0":
                kept.append(f"  flow_control = {sif['flow_control']}")

        try:
            config_path.write_text("\n".join(kept) + "\n")
            QMessageBox.information(self, "Saved", "Serial interface settings saved. Restart to apply.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _load_serial_interfaces(self):
        config_path = Path.home() / ".reticulum" / "config"
        if not config_path.exists():
            return
        try:
            text = config_path.read_text()
            lines = text.splitlines()
            self.serial_interfaces = []
            current = None
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("[[") and stripped.endswith("]]"):
                    sec_name = stripped[2:-2].strip()
                    if "SerialInterface" in sec_name or "KISSInterface" in sec_name:
                        current = {"type": "KISSInterface" if "KISS" in sec_name else "SerialInterface",
                                   "port": "/dev/ttyUSB0", "speed": "115200", "flow_control": "0"}
                    else:
                        current = None
                    continue
                if current is None:
                    continue
                if stripped.startswith("type "):
                    current["type"] = stripped.split("=", 1)[1].strip()
                elif stripped.startswith("port "):
                    current["port"] = stripped.split("=", 1)[1].strip()
                elif stripped.startswith("speed "):
                    current["speed"] = stripped.split("=", 1)[1].strip()
                elif stripped.startswith("flow_control "):
                    current["flow_control"] = stripped.split("=", 1)[1].strip()
                elif stripped.startswith("[[") and stripped.endswith("]]"):
                    if current:
                        self.serial_interfaces.append(current)
                    current = None
            if current:
                self.serial_interfaces.append(current)
            self._refresh_serial_table()
        except:
            pass

    def _restart_application(self):
        if QMessageBox.question(self, "Restart", "Restart application now?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                os.execv(sys.executable, [sys.executable, "-m", "src.main"])
            except:
                QApplication.quit()
