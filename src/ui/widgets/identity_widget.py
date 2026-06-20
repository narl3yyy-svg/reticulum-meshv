"""Identity tab — view, rename, and manage RNS identity."""

import RNS
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt
from src.config.theme import MeshTheme


class IdentityWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.rns_node = getattr(backend, 'rns_node', None)
        self.lxmf_messenger = getattr(backend, 'lxmf_messenger', None)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Identity")
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

        # === Display Name ===
        name_group = QGroupBox("Display Name")
        name_group.setStyleSheet(group_style())
        name_layout = QVBoxLayout()

        name_desc = QLabel("This name is shown to other nodes when you announce.")
        name_desc.setWordWrap(True)
        name_desc.setStyleSheet(f"color: {MeshTheme.TEXT_MUTED}; font-size: 12px; background: transparent;")
        name_layout.addWidget(name_desc)

        name_row = QHBoxLayout()
        self.name_input = QLineEdit(self.backend.get_display_name() if hasattr(self.backend, 'get_display_name') else "")
        self.name_input.setPlaceholderText("Enter your display name...")
        self.name_input.setStyleSheet(f"""
            QLineEdit {{ background-color: {MeshTheme.INPUT_BG}; color: {MeshTheme.TEXT};
                border: 1px solid {MeshTheme.INPUT_BORDER}; border-radius: 12px; padding: 10px 14px; font-size: 14px; }}
            QLineEdit:focus {{ border: 2px solid {MeshTheme.FOCUS}; }}
        """)
        name_row.addWidget(self.name_input, 1)

        save_name_btn = QPushButton("Save")
        save_name_btn.clicked.connect(self._save_name)
        name_row.addWidget(save_name_btn)

        name_layout.addLayout(name_row)
        name_group.setLayout(name_layout)
        layout.addWidget(name_group)

        # === Identity Hash ===
        hash_group = QGroupBox("Identity Hash")
        hash_group.setStyleSheet(group_style())
        hash_layout = QVBoxLayout()

        hash_desc = QLabel("Your RNS identity hash. Share this so others can send you messages.")
        hash_desc.setWordWrap(True)
        hash_desc.setStyleSheet(f"color: {MeshTheme.TEXT_MUTED}; font-size: 12px; background: transparent;")
        hash_layout.addWidget(hash_desc)

        self.hash_label = QLabel()
        self.hash_label.setWordWrap(True)
        self.hash_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.hash_label.setStyleSheet(f"font-family: 'JetBrains Mono', monospace; font-size: 13px; color: {MeshTheme.ACCENT}; background: {MeshTheme.SURFACE}; padding: 12px; border-radius: 12px;")
        hash_layout.addWidget(self.hash_label)

        # LXMF delivery hash
        self.lxmf_hash_label = QLabel()
        self.lxmf_hash_label.setWordWrap(True)
        self.lxmf_hash_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lxmf_hash_label.setStyleSheet(f"font-family: 'JetBrains Mono', monospace; font-size: 13px; color: {MeshTheme.TEXT_MUTED}; background: {MeshTheme.SURFACE}; padding: 12px; border-radius: 12px;")
        hash_layout.addWidget(self.lxmf_hash_label)

        hash_btn_row = QHBoxLayout()
        copy_hash_btn = QPushButton("Copy Identity Hash")
        copy_hash_btn.clicked.connect(self._copy_hash)
        hash_btn_row.addWidget(copy_hash_btn)

        copy_lxmf_btn = QPushButton("Copy LXMF Hash")
        copy_lxmf_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {MeshTheme.ACCENT};
                border: 1px solid {MeshTheme.ACCENT}; border-radius: 12px; padding: 10px 20px; font-size: 13px; }}
            QPushButton:hover {{ background-color: {MeshTheme.ACCENT}20; }}
        """)
        copy_lxmf_btn.clicked.connect(self._copy_lxmf_hash)
        hash_btn_row.addWidget(copy_lxmf_btn)

        hash_layout.addLayout(hash_btn_row)
        hash_group.setLayout(hash_layout)
        layout.addWidget(hash_group)

        # === Identity File ===
        file_group = QGroupBox("Identity File")
        file_group.setStyleSheet(group_style())
        file_layout = QVBoxLayout()

        file_desc = QLabel("Your identity is stored as a key file. You can export it to back up or transfer to another device.")
        file_desc.setWordWrap(True)
        file_desc.setStyleSheet(f"color: {MeshTheme.TEXT_MUTED}; font-size: 12px; background: transparent;")
        file_layout.addWidget(file_desc)

        if self.rns_node:
            identity_path = self.rns_node.app_config_dir / "identity.key"
            path_label = QLabel(f"Location: {identity_path}")
            path_label.setWordWrap(True)
            path_label.setStyleSheet(f"font-family: 'JetBrains Mono', monospace; font-size: 11px; color: {MeshTheme.TEXT_DIM}; background: transparent;")
            file_layout.addWidget(path_label)

        file_btn_row = QHBoxLayout()

        export_btn = QPushButton("Export Identity")
        export_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {MeshTheme.ACCENT};
                border: 1px solid {MeshTheme.ACCENT}; border-radius: 12px; padding: 10px 20px; font-size: 13px; }}
            QPushButton:hover {{ background-color: {MeshTheme.ACCENT}20; }}
        """)
        export_btn.clicked.connect(self._export_identity)
        file_btn_row.addWidget(export_btn)

        file_layout.addLayout(file_btn_row)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # === Announce ===
        announce_group = QGroupBox("Announce")
        announce_group.setStyleSheet(group_style())
        announce_layout = QVBoxLayout()

        announce_desc = QLabel("Announce your presence on the Reticulum network. Other nodes will see your display name and hash.")
        announce_desc.setWordWrap(True)
        announce_desc.setStyleSheet(f"color: {MeshTheme.TEXT_MUTED}; font-size: 12px; background: transparent;")
        announce_layout.addWidget(announce_desc)

        announce_btn = QPushButton("Announce Now")
        announce_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {MeshTheme.ACTION_PRIMARY}; color: white; border: none;
                border-radius: 12px; padding: 10px 24px; font-size: 14px; font-weight: 600; }}
            QPushButton:hover {{ background-color: {MeshTheme.ACTION_PRIMARY_HOVER}; }}
        """)
        announce_btn.clicked.connect(self._announce)
        announce_layout.addWidget(announce_btn)

        announce_group.setLayout(announce_layout)
        layout.addWidget(announce_group)

        layout.addStretch()

        self._update_hashes()

    def _update_hashes(self):
        if self.rns_node:
            self.hash_label.setText(f"RNS Identity:\n{self.rns_node.get_identity_hash()}")
        else:
            self.hash_label.setText("RNS Identity: Not available")

        if self.lxmf_messenger and hasattr(self.lxmf_messenger, 'get_delivery_hash'):
            lxmf_hash = self.lxmf_messenger.get_delivery_hash()
            self.lxmf_hash_label.setText(f"LXMF Delivery:\n{lxmf_hash}")
        else:
            self.lxmf_hash_label.setText("LXMF Delivery: Not available")

    def _save_name(self):
        name = self.name_input.text().strip()
        if name and hasattr(self.backend, 'set_display_name'):
            self.backend.set_display_name(name)
            QMessageBox.information(self, "Saved", f"Display name set to: {name}")

    def _copy_hash(self):
        if self.rns_node:
            QApplication.clipboard().setText(self.rns_node.get_identity_hash())
            QMessageBox.information(self, "Copied", "Identity hash copied to clipboard.")

    def _copy_lxmf_hash(self):
        if self.lxmf_messenger and hasattr(self.lxmf_messenger, 'get_delivery_hash'):
            QApplication.clipboard().setText(self.lxmf_messenger.get_delivery_hash())
            QMessageBox.information(self, "Copied", "LXMF hash copied to clipboard.")

    def _export_identity(self):
        from PyQt6.QtWidgets import QFileDialog
        if not self.rns_node or not self.rns_node.identity:
            QMessageBox.warning(self, "Error", "No identity to export.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Identity", "identity.key", "Key files (*.key)")
        if path:
            try:
                self.rns_node.identity.to_file(path)
                QMessageBox.information(self, "Exported", f"Identity exported to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _announce(self):
        if self.backend and hasattr(self.backend, 'announce_now'):
            if self.backend.announce_now():
                QMessageBox.information(self, "Announced", "You are now visible on the Reticulum network.")
            else:
                QMessageBox.warning(self, "Error", "Could not announce.")
