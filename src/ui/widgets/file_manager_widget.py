"""File transfer widget with proper folder zipping (preserves original name)."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QFileDialog, QProgressBar, QLabel,
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication
from pathlib import Path
import zipfile
import tempfile


class FileTransferThread(QThread):
    progress_updated = pyqtSignal(int, int, int)
    transfer_complete = pyqtSignal(str)
    transfer_failed = pyqtSignal(str, str)

    def __init__(self, file_manager, file_path, destination):
        super().__init__()
        self.file_manager = file_manager
        self.file_path = file_path
        self.destination = destination

    def run(self):
        try:
            success = self.file_manager.send_file(self.file_path, self.destination, self._on_progress)
            if success:
                self.transfer_complete.emit(self.file_path)
            else:
                self.transfer_failed.emit("Transfer returned failure", self.file_path)
        except Exception as e:
            self.transfer_failed.emit(str(e), self.file_path)

    def _on_progress(self, percentage, current, total):
        self.progress_updated.emit(int(current), int(total), int(percentage))


class FileManagerWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.file_transfer_manager = backend.file_transfer_manager
        self.rns_node = backend.rns_node
        self.transfer_thread = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        identity_group = QGroupBox("Your Identity (share this hash so others can send you files)")
        identity_group.setStyleSheet("QGroupBox { font-weight: bold; } ")
        identity_layout = QHBoxLayout()

        self.identity_label = QLabel(self.rns_node.get_short_identity_hash())
        self.identity_label.setStyleSheet("font-family: monospace; font-size: 14px; padding: 4px; background: #2a2a2a; border-radius: 4px;")
        self.identity_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        copy_btn = QPushButton("📋 Copy Hash")
        copy_btn.setMinimumHeight(32)
        copy_btn.clicked.connect(self._copy_identity)

        full_hash_btn = QPushButton("Show Full Hash")
        full_hash_btn.setMinimumHeight(32)
        full_hash_btn.clicked.connect(self._show_full_identity)

        identity_layout.addWidget(QLabel("Hash:"), 0)
        identity_layout.addWidget(self.identity_label, 1)
        identity_layout.addWidget(copy_btn, 0)
        identity_layout.addWidget(full_hash_btn, 0)
        identity_group.setLayout(identity_layout)
        layout.addWidget(identity_group)

        tip = QLabel("💡 Click <b>Copy Hash</b> or <b>Show Full Hash</b> to get your identity. Paste the recipient's full hash below.")
        tip.setWordWrap(True)
        tip.setStyleSheet("color: #aaa; font-size: 12px;")
        layout.addWidget(tip)

        title = QLabel("Large File Transfers")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-top: 12px;")
        layout.addWidget(title)

        subtitle = QLabel("Folders are sent as real folders (zipped internally + auto-extracted on receive)")
        layout.addWidget(subtitle)

        file_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select a file or folder...")
        self.file_path_input.setReadOnly(True)

        browse_file_btn = QPushButton("Browse File")
        browse_file_btn.clicked.connect(self._browse_file)

        browse_folder_btn = QPushButton("Browse Folder")
        browse_folder_btn.clicked.connect(self._browse_folder)

        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(browse_file_btn)
        file_layout.addWidget(browse_folder_btn)
        layout.addLayout(file_layout)

        dest_layout = QHBoxLayout()
        dest_label = QLabel("Destination Hash:")
        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("Paste the recipient's full identity hash here")
        dest_layout.addWidget(dest_label, 0)
        dest_layout.addWidget(self.dest_input, 1)
        layout.addLayout(dest_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(20)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        send_btn = QPushButton("📤 Send over Mesh")
        send_btn.setMinimumHeight(44)
        send_btn.setStyleSheet("font-size: 15px; font-weight: bold;")
        send_btn.clicked.connect(self._send_file)
        layout.addWidget(send_btn)

        layout.addWidget(QLabel("Transfer History"))
        self.transfers_table = QTableWidget()
        self.transfers_table.setColumnCount(4)
        self.transfers_table.setHorizontalHeaderLabels(["Name", "To", "Progress", "Status"])
        self.transfers_table.setMaximumHeight(180)
        self.transfers_table.setAlternatingRowColors(True)
        layout.addWidget(self.transfers_table)

        layout.addStretch()

    def _copy_identity(self):
        clipboard = QApplication.clipboard()
        hash_to_copy = self.rns_node.get_identity_hash()
        clipboard.setText(hash_to_copy)
        expected = self.rns_node.hash_length
        QMessageBox.information(self, "Copied", f"Identity hash copied ({expected} characters)")

    def _show_full_identity(self):
        full = self.rns_node.get_identity_hash()
        expected = self.rns_node.hash_length
        QMessageBox.information(self, "Your Identity Hash ({expected} chars)", full)

    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select file to send")
        if file_path:
            self.file_path_input.setText(file_path)
            self.file_path_input.setProperty("is_folder", False)

    def _browse_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select folder to send")
        if folder_path:
            self.file_path_input.setText(folder_path)
            self.file_path_input.setProperty("is_folder", True)

    def _send_file(self):
        selected_path = self.file_path_input.text().strip()
        destination = self.dest_input.text().strip().lower()

        if not selected_path:
            QMessageBox.warning(self, "Error", "Please select a file or folder first.")
            return

        if not destination:
            QMessageBox.warning(self, "Error", "Please enter the recipient's Destination Hash.")
            return

        expected_len = self.rns_node.hash_length
        if len(destination) != expected_len or not all(c in "0123456789abcdef" for c in destination):
            QMessageBox.warning(self, "Invalid Hash", f"Must be exactly {expected_len} hex characters.")
            return

        path_obj = Path(selected_path)
        is_folder = bool(self.file_path_input.property("is_folder")) or path_obj.is_dir()

        send_path = selected_path
        display_name = path_obj.name

        if is_folder:
            # Create zip with original folder name
            try:
                zip_name = path_obj.name + ".zip"
                temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip", prefix=path_obj.name + "_")
                temp_zip_path = Path(temp_zip.name)
                temp_zip.close()

                with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file in path_obj.rglob("*"):
                        if file.is_file():
                            arcname = file.relative_to(path_obj)
                            zipf.write(file, arcname)

                send_path = str(temp_zip_path)
                display_name = zip_name   # show as FolderName.zip in history
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to prepare folder: {str(e)}")
                return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Transfer starting...")

        row = self.transfers_table.rowCount()
        self.transfers_table.insertRow(row)
        self.transfers_table.setItem(row, 0, QTableWidgetItem(display_name))
        self.transfers_table.setItem(row, 1, QTableWidgetItem(destination[:12] + "..."))
        self.transfers_table.setItem(row, 2, QTableWidgetItem("0%"))
        self.transfers_table.setItem(row, 3, QTableWidgetItem("Sending..."))

        self.transfer_thread = FileTransferThread(self.file_transfer_manager, send_path, destination)
        self.transfer_thread.progress_updated.connect(lambda cur, tot, pct: self._on_progress(cur, tot, pct, row))
        self.transfer_thread.transfer_complete.connect(lambda fp: self._on_complete(fp, row, is_folder, path_obj.name))
        self.transfer_thread.transfer_failed.connect(lambda err, fp: self._on_failed(err, fp, row))
        self.transfer_thread.start()

    def _on_progress(self, current, total, percentage, row):
        self.progress_bar.setValue(percentage)
        mb_current = current / (1024 * 1024)
        mb_total = total / (1024 * 1024)
        self.status_label.setText(f"Transferring: {mb_current:.1f} MB / {mb_total:.1f} MB ({percentage}%)")
        if row < self.transfers_table.rowCount():
            self.transfers_table.setItem(row, 2, QTableWidgetItem(f"{percentage}%"))

    def _on_complete(self, file_path, row, was_folder=False, original_name=""):
        self.status_label.setText("✓ Done!")
        self.progress_bar.setValue(100)
        if row < self.transfers_table.rowCount():
            self.transfers_table.setItem(row, 3, QTableWidgetItem("Completed"))

        if was_folder:
            msg = f"Folder sent successfully (will appear as folder on recipient side)"
        else:
            msg = f"File sent: {Path(file_path).name}"
        QMessageBox.information(self, "Success", msg)

    def _on_failed(self, error, file_path, row):
        self.status_label.setText(f"✗ Failed")
        if row < self.transfers_table.rowCount():
            self.transfers_table.setItem(row, 3, QTableWidgetItem("Failed"))
        QMessageBox.critical(self, "Error", str(error))
