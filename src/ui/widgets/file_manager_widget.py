"""Files tab — shows downloads directory and received files."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from pathlib import Path
from src.config.theme import MeshTheme


class FileManagerWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.rns_node = getattr(backend, 'rns_node', None)
        self.downloads_dir = getattr(backend, 'downloads_dir', Path.home() / "Downloads" / "RMESHV")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Files")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {MeshTheme.TEXT}; background: transparent;")
        layout.addWidget(title)

        subtitle = QLabel("Received files are saved to your downloads folder.")
        subtitle.setStyleSheet(f"color: {MeshTheme.TEXT_MUTED}; font-size: 13px; background: transparent;")
        layout.addWidget(subtitle)

        # Download path
        path_row = QHBoxLayout()
        path_label = QLabel("Download folder:")
        path_label.setStyleSheet(f"color: {MeshTheme.TEXT}; font-weight: 600; background: transparent;")
        path_row.addWidget(path_label)

        self.path_display = QLabel(str(self.downloads_dir))
        self.path_display.setStyleSheet(f"font-family: 'JetBrains Mono', monospace; font-size: 12px; color: {MeshTheme.ACCENT}; background: transparent;")
        path_row.addWidget(self.path_display, 1)

        browse_btn = QPushButton("Change...")
        browse_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {MeshTheme.TEXT_MUTED};
                border: 1px solid {MeshTheme.BORDER}; border-radius: 12px; padding: 8px 16px; font-size: 12px; }}
            QPushButton:hover {{ background-color: {MeshTheme.SURFACE_VARIANT}; color: {MeshTheme.TEXT}; }}
        """)
        browse_btn.clicked.connect(self._change_folder)
        path_row.addWidget(browse_btn)

        open_btn = QPushButton("Open Folder")
        open_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {MeshTheme.ACCENT};
                border: 1px solid {MeshTheme.ACCENT}; border-radius: 12px; padding: 8px 16px; font-size: 12px; }}
            QPushButton:hover {{ background-color: {MeshTheme.ACCENT}20; }}
        """)
        open_btn.clicked.connect(self._open_folder)
        path_row.addWidget(open_btn)

        layout.addLayout(path_row)

        # File table
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(3)
        self.file_table.setHorizontalHeaderLabels(["Filename", "Size", "Modified"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.file_table.setStyleSheet(f"""
            QTableWidget {{ background: transparent; border: 1px solid {MeshTheme.BORDER_CARD}; border-radius: 12px; }}
            QTableWidget::item {{ color: {MeshTheme.TEXT}; padding: 6px 8px; }}
            QTableWidget::item:selected {{ background: {MeshTheme.ACTION_PRIMARY}; color: white; }}
            QHeaderView::section {{ background: {MeshTheme.SURFACE}; color: {MeshTheme.TEXT_MUTED};
                border: none; border-bottom: 1px solid {MeshTheme.BORDER}; padding: 6px 8px; font-weight: 600; font-size: 12px; }}
        """)
        layout.addWidget(self.file_table, 1)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_files)
        layout.addWidget(refresh_btn)

        self._refresh_files()

    def _refresh_files(self):
        self.file_table.setRowCount(0)
        if not self.downloads_dir.exists():
            return
        try:
            files = sorted(self.downloads_dir.iterdir(), key=lambda f: f.stat().st_mtime if f.is_file() else 0, reverse=True)
            for f in files:
                if not f.is_file():
                    continue
                row = self.file_table.rowCount()
                self.file_table.insertRow(row)
                self.file_table.setItem(row, 0, QTableWidgetItem(f.name))
                size = f.stat().st_size
                size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"
                self.file_table.setItem(row, 1, QTableWidgetItem(size_str))
                import time
                mod = time.strftime("%Y-%m-%d %H:%M", time.localtime(f.stat().st_mtime))
                self.file_table.setItem(row, 2, QTableWidgetItem(mod))
        except:
            pass

    def _change_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose download folder")
        if folder:
            self.downloads_dir = Path(folder)
            if hasattr(self.backend, 'downloads_dir'):
                self.backend.downloads_dir = Path(folder)
            self.path_display.setText(folder)
            self._refresh_files()

    def _open_folder(self):
        import subprocess
        try:
            subprocess.Popen(["xdg-open", str(self.downloads_dir)])
        except:
            pass
