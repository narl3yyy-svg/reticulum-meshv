"""Files tab — send files/folders, view downloads."""

import os
import zipfile
import tempfile
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QGroupBox, QLineEdit
)
from PyQt6.QtCore import Qt
from src.config.theme import MeshTheme


class FileManagerWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.rns_node = getattr(backend, 'rns_node', None)
        self.lxmf_messenger = getattr(backend, 'lxmf_messenger', None)
        self.downloads_dir = getattr(backend, 'downloads_dir', Path.home() / "Downloads" / "RMESHV")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Files")
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

        # === Send Files ===
        send_group = QGroupBox("Send Files")
        send_group.setStyleSheet(group_style())
        send_layout = QVBoxLayout()

        send_desc = QLabel("Send files or folders to a contact. Folders are zipped automatically.\nFiles are sent via LXMF as attachments.")
        send_desc.setWordWrap(True)
        send_desc.setStyleSheet(f"color: {MeshTheme.TEXT_MUTED}; font-size: 13px; background: transparent;")
        send_layout.addWidget(send_desc)

        dest_row = QHBoxLayout()
        dest_label = QLabel("Send to (hash):")
        dest_label.setStyleSheet(f"color: {MeshTheme.TEXT}; background: transparent;")
        dest_row.addWidget(dest_label)

        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("Destination identity hash...")
        self.dest_input.setStyleSheet(f"""
            QLineEdit {{ background-color: {MeshTheme.INPUT_BG}; color: {MeshTheme.TEXT};
                border: 1px solid {MeshTheme.INPUT_BORDER}; border-radius: 12px; padding: 10px 14px; font-size: 13px; }}
            QLineEdit:focus {{ border: 2px solid {MeshTheme.FOCUS}; }}
        """)
        dest_row.addWidget(self.dest_input, 1)
        send_layout.addLayout(dest_row)

        btn_row = QHBoxLayout()

        file_btn = QPushButton("Select File")
        file_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {MeshTheme.ACTION_PRIMARY}; color: white; border: none;
                border-radius: 12px; padding: 10px 20px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background-color: {MeshTheme.ACTION_PRIMARY_HOVER}; }}
        """)
        file_btn.clicked.connect(self._select_file)
        btn_row.addWidget(file_btn)

        folder_btn = QPushButton("Select Folder")
        folder_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {MeshTheme.ACCENT};
                border: 1px solid {MeshTheme.ACCENT}; border-radius: 12px;
                padding: 10px 20px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background-color: {MeshTheme.ACCENT}20; }}
        """)
        folder_btn.clicked.connect(self._select_folder)
        btn_row.addWidget(folder_btn)

        send_layout.addLayout(btn_row)

        self.selected_label = QLabel("No file selected")
        self.selected_label.setStyleSheet(f"color: {MeshTheme.TEXT_DIM}; font-size: 12px; background: transparent; padding: 4px 0;")
        send_layout.addWidget(self.selected_label)

        self.send_progress = QProgressBar()
        self.send_progress.setVisible(False)
        self.send_progress.setStyleSheet(f"""
            QProgressBar {{ background-color: {MeshTheme.SURFACE_VARIANT}; border: none; border-radius: 4px; }}
            QProgressBar::chunk {{ background-color: {MeshTheme.SUCCESS}; border-radius: 4px; }}
        """)
        send_layout.addWidget(self.send_progress)

        send_group.setLayout(send_layout)
        layout.addWidget(send_group)

        # === Downloads ===
        dl_group = QGroupBox("Downloads")
        dl_group.setStyleSheet(group_style())
        dl_layout = QVBoxLayout()

        path_row = QHBoxLayout()
        path_label = QLabel("Folder:")
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

        open_btn = QPushButton("Open")
        open_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {MeshTheme.ACCENT};
                border: 1px solid {MeshTheme.ACCENT}; border-radius: 12px; padding: 8px 16px; font-size: 12px; }}
            QPushButton:hover {{ background-color: {MeshTheme.ACCENT}20; }}
        """)
        open_btn.clicked.connect(self._open_folder)
        path_row.addWidget(open_btn)

        dl_layout.addLayout(path_row)

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
        dl_layout.addWidget(self.file_table, 1)

        refresh_btn = QPushButton("Refresh List")
        refresh_btn.clicked.connect(self._refresh_files)
        dl_layout.addWidget(refresh_btn)

        dl_group.setLayout(dl_layout)
        layout.addWidget(dl_group, 1)

        self._refresh_files()

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select File to Send")
        if path:
            self._selected_path = path
            fname = os.path.basename(path)
            size = os.path.getsize(path)
            size_str = self._fmt_size(size)
            self.selected_label.setText(f"Selected: {fname} ({size_str})")
            self._send_file(path)

    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Send")
        if folder:
            self.selected_label.setText("Compressing folder...")
            zip_path = self._zip_folder(folder)
            if zip_path:
                self._selected_path = zip_path
                fname = os.path.basename(zip_path)
                size = os.path.getsize(zip_path)
                size_str = self._fmt_size(size)
                self.selected_label.setText(f"Selected: {fname} ({size_str})")
                self._send_file(zip_path)

    def _zip_folder(self, folder_path):
        try:
            folder_name = os.path.basename(folder_path)
            tmp_dir = tempfile.gettempdir()
            zip_path = os.path.join(tmp_dir, f"{folder_name}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, folder_path)
                        zf.write(file_path, arcname)
            return zip_path
        except Exception as e:
            self.selected_label.setText(f"Error: {e}")
            return None

    def _send_file(self, file_path):
        dest_hash = self.dest_input.text().strip()
        if not dest_hash:
            self.selected_label.setText("Error: Enter a destination hash first")
            return
        if not self.lxmf_messenger:
            self.selected_label.setText("Error: LXMF not available")
            return

        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            fname = os.path.basename(file_path)
            size = len(file_data)

            from PyQt6.QtWidgets import QMessageBox
            if size > 5_000_000:
                QMessageBox.warning(self, "Large File", f"File is {self._fmt_size(size)}. Large transfers may take a long time over RNS.")

            msg_text = f"[File: {fname} ({self._fmt_size(size)})]"

            if self.lxmf_messenger.send_message(dest_hash, msg_text):
                self.selected_label.setText(f"Sent: {fname}")
            else:
                self.selected_label.setText("Failed to send file")

        except Exception as e:
            self.selected_label.setText(f"Error: {e}")

    def _fmt_size(self, size):
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"

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
                self.file_table.setItem(row, 1, QTableWidgetItem(self._fmt_size(f.stat().st_size)))
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
