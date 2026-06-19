"""Settings widget — identity, downloads, interfaces, privacy."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFileDialog, QCheckBox, QGroupBox, QMessageBox, QComboBox,
    QScrollArea
)
from PyQt6.QtCore import Qt
from pathlib import Path
from src.config.theme import MeshTheme


class SettingsWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.rns_node = getattr(backend, 'rns_node', None)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(24, 24, 24, 24)
        scroll_layout.setSpacing(16)

        title = QLabel("Settings")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {MeshTheme.TEXT}; background: transparent;")
        scroll_layout.addWidget(title)

        def group_style():
            return f"""
                QGroupBox {{ color: {MeshTheme.TEXT_MUTED}; font-size: 12px;
                    border: 1px solid {MeshTheme.BORDER_CARD}; border-radius: 16px; margin-top: 20px;
                    padding: 16px; }}
                QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left;
                    padding: 4px 12px; color: {MeshTheme.TEXT_MUTED}; font-size: 12px; }}
            """

        # === Identity ===
        id_group = QGroupBox("Your Identity")
        id_group.setStyleSheet(group_style())
        id_layout = QVBoxLayout()

        self.identity_label = QLabel()
        self.identity_label.setStyleSheet(f"font-family: 'JetBrains Mono', monospace; background: {MeshTheme.SURFACE}; padding: 12px; border-radius: 12px; font-size: 13px; color: {MeshTheme.TEXT};")
        self._update_identity_display()
        id_layout.addWidget(self.identity_label)

        announce_btn = QPushButton("Announce on Network")
        announce_btn.clicked.connect(self._announce_myself)
        id_layout.addWidget(announce_btn)

        note = QLabel("Announcing makes you visible to other nodes on the Reticulum network.")
        note.setStyleSheet(f"color: {MeshTheme.TEXT_DIM}; font-size: 12px; background: transparent;")
        id_layout.addWidget(note)

        id_group.setLayout(id_layout)
        scroll_layout.addWidget(id_group)

        # === Downloads ===
        dl_group = QGroupBox("Downloads")
        dl_group.setStyleSheet(group_style())
        dl_layout = QVBoxLayout()

        self.download_path = QLineEdit()
        self.download_path.setReadOnly(True)
        if hasattr(self.backend, 'downloads_dir'):
            self.download_path.setText(str(self.backend.downloads_dir))

        browse_btn = QPushButton("Change Download Folder...")
        browse_btn.clicked.connect(self._change_download_folder)

        label = QLabel("Received files are saved to:")
        label.setStyleSheet(f"color: {MeshTheme.TEXT}; background: transparent;")
        dl_layout.addWidget(label)
        dl_layout.addWidget(self.download_path)
        dl_layout.addWidget(browse_btn)
        dl_group.setLayout(dl_layout)
        scroll_layout.addWidget(dl_group)

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
                border: 1px solid {MeshTheme.INPUT_BORDER}; border-radius: 12px;
                padding: 10px 14px; font-size: 13px;
            }}
            QComboBox::drop-down {{ border: none; padding-right: 8px; }}
            QComboBox::item:selected {{ background-color: {MeshTheme.ACTION_PRIMARY}; color: white; }}
        """)
        current_filter = self.backend.get_message_filter() if hasattr(self.backend, 'get_message_filter') else "all"
        idx = self.filter_combo.findData(current_filter)
        if idx >= 0:
            self.filter_combo.setCurrentIndex(idx)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        msg_layout.addWidget(self.filter_combo)

        filter_note = QLabel("Trusted contacts can be managed from the Contacts tab.\nBlocked senders are silently ignored.")
        filter_note.setStyleSheet(f"color: {MeshTheme.TEXT_DIM}; font-size: 12px; background: transparent;")
        filter_note.setWordWrap(True)
        msg_layout.addWidget(filter_note)

        msg_group.setLayout(msg_layout)
        scroll_layout.addWidget(msg_group)

        scroll_layout.addStretch()

        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setWidget(scroll_widget)
        sa.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        layout.addWidget(sa)

    def _update_identity_display(self):
        if self.rns_node and self.rns_node.identity:
            try:
                full_hash = self.rns_node.get_identity_hash()
                self.identity_label.setText(f"Identity Hash:\n{full_hash}")
            except:
                self.identity_label.setText("Could not load identity hash.")
        else:
            self.identity_label.setText("Identity not loaded.")

    def _announce_myself(self):
        if self.backend and hasattr(self.backend, 'announce_now'):
            if self.backend.announce_now():
                QMessageBox.information(self, "Announced", "You are now visible on the Reticulum network.")
            else:
                QMessageBox.warning(self, "Error", "Could not announce (Reticulum not ready).")

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
            sb.showMessage(f"Message filter: {mode}", 3000)

    def _find_status_bar(self):
        p = self.parent()
        while p:
            if hasattr(p, 'statusBar'):
                return p.statusBar()
            p = p.parent()
        return None
