"""Settings widget for Reticulum Mesh."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFileDialog, QCheckBox, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt
from pathlib import Path


class SettingsWidget(QWidget):
    """Application settings."""
    
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)
        
        # Downloads
        dl_group = QGroupBox("File Downloads")
        dl_layout = QVBoxLayout()
        
        self.download_path = QLineEdit()
        self.download_path.setReadOnly(True)
        if hasattr(self.backend, 'downloads_dir'):
            self.download_path.setText(str(self.backend.downloads_dir))
        
        browse_btn = QPushButton("Change Download Folder...")
        browse_btn.clicked.connect(self._change_download_folder)
        
        dl_layout.addWidget(QLabel("Received files will be saved to:"))
        dl_layout.addWidget(self.download_path)
        dl_layout.addWidget(browse_btn)
        dl_group.setLayout(dl_layout)
        layout.addWidget(dl_group)
        
        # Identity
        id_group = QGroupBox("Identity")
        id_layout = QVBoxLayout()
        
        backup_btn = QPushButton("Backup Identity (copy identity.key)")
        backup_btn.clicked.connect(self._backup_identity)
        
        id_layout.addWidget(QLabel("Your permanent mesh identity is stored in:")
        id_layout.addWidget(QLabel(str(self.backend.app_config_dir / "identity.key")))
        id_layout.addWidget(backup_btn)
        id_group.setLayout(id_layout)
        layout.addWidget(id_group)
        
        # Behavior
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout()
        
        self.auto_accept = QCheckBox("Auto-accept incoming files")
        self.auto_accept.setChecked(True)
        behavior_layout.addWidget(self.auto_accept)
        
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)
        
        layout.addStretch()
    
    def _change_download_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose download folder")
        if folder:
            self.download_path.setText(folder)
            if hasattr(self.backend, 'downloads_dir'):
                self.backend.downloads_dir = Path(folder)
            QMessageBox.information(self, "Updated", "Download folder changed.")
    
    def _backup_identity(self):
        QMessageBox.information(
            self, 
            "Backup Identity", 
            "Your identity.key file is at:\n\n" + str(self.backend.app_config_dir / "identity.key") + 
            "\n\nCopy this file to back up your permanent mesh identity."
        )
