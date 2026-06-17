"""File transfer widget with easy identity sharing."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QFileDialog, QProgressBar, QLabel,
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication
from pathlib import Path
import asyncio


class FileTransferThread(QThread):
    """Background file transfer thread."""
    
    progress_updated = pyqtSignal(int, int, int)
    transfer_complete = pyqtSignal(str)
    transfer_failed = pyqtSignal(str, str)
    
    def __init__(self, file_manager, file_path, destination):
        super().__init__()
        self.file_manager = file_manager
        self.file_path = file_path
        self.destination = destination
    
    def run(self):
        """Execute transfer."""
        try:
            asyncio.run(
                self.file_manager.send_file(
                    self.file_path,
                    self.destination,
                    self._on_progress
                )
            )
            self.transfer_complete.emit(self.file_path)
        except Exception as e:
            self.transfer_failed.emit(str(e), self.file_path)
    
    def _on_progress(self, percentage, current, total):
        """Emit progress."""
        self.progress_updated.emit(int(current), int(total), int(percentage))


class FileManagerWidget(QWidget):
    """File sharing and transfer widget."""
    
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.file_transfer_manager = backend.file_transfer_manager
        self.rns_node = backend.rns_node
        self.transfer_thread = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # === My Identity Section (makes it easy to share) ===
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
        
        # Helpful tip
        tip = QLabel("💡 Tip: Give the hash above to people who want to send files to you. "
                     "They paste it into 'Destination Hash'. You can also use the full 64-char hash.")
        tip.setWordWrap(True)
        tip.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(tip)
        
        # Title
        title = QLabel("Large File Transfers")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-top: 12px;")
        layout.addWidget(title)
        
        subtitle = QLabel("Chunked transfers over Reticulum mesh (real implementation coming soon - currently demo mode)")
        layout.addWidget(subtitle)
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select a file to send...")
        self.file_path_input.setReadOnly(True)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_file)
        
        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)
        
        # Destination
        dest_layout = QHBoxLayout()
        dest_label = QLabel("Destination Hash:")
        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("Paste recipient's identity or destination hash here (64 hex chars)")
        dest_layout.addWidget(dest_label, 0)
        dest_layout.addWidget(self.dest_input, 1)
        layout.addLayout(dest_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(20)
        layout.addWidget(self.progress_bar)
        
        # Status
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # Send button
        send_btn = QPushButton("📤 Send File over Mesh")
        send_btn.setMinimumHeight(44)
        send_btn.setStyleSheet("font-size: 15px; font-weight: bold;")
        send_btn.clicked.connect(self._send_file)
        layout.addWidget(send_btn)
        
        # Recent transfers table
        layout.addWidget(QLabel("Transfer History"))
        self.transfers_table = QTableWidget()
        self.transfers_table.setColumnCount(4)
        self.transfers_table.setHorizontalHeaderLabels(["File", "Destination", "Progress", "Status"])
        self.transfers_table.setMaximumHeight(180)
        self.transfers_table.setAlternatingRowColors(True)
        layout.addWidget(self.transfers_table)
        
        layout.addStretch()
    
    def _copy_identity(self):
        """Copy short or full identity hash to clipboard."""
        clipboard = QApplication.clipboard()
        hash_to_copy = self.rns_node.get_identity_hash()
        clipboard.setText(hash_to_copy)
        QMessageBox.information(self, "Copied", "Identity hash copied to clipboard!\n\nShare it with others so they can send you files.")
    
    def _show_full_identity(self):
        """Show the complete 64-character identity hash."""
        full = self.rns_node.get_identity_hash()
        QMessageBox.information(
            self, 
            "Your Full Identity Hash", 
            f"{full}\n\nLength: {len(full)} characters\n\nThis is your permanent address on the Reticulum mesh."
        )
    
    def _browse_file(self):
        """Browse for file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select file to send")
        if file_path:
            self.file_path_input.setText(file_path)
    
    def _send_file(self):
        """Send selected file."""
        file_path = self.file_path_input.text().strip()
        destination = self.dest_input.text().strip().lower()
        
        if not file_path:
            QMessageBox.warning(self, "Error", "Please select a file first.")
            return
        
        if not destination:
            QMessageBox.warning(self, "Error", "Please enter the recipient's Destination Hash.")
            return
        
        # Basic validation
        if len(destination) != 64 or not all(c in "0123456789abcdef" for c in destination):
            QMessageBox.warning(
                self, "Invalid Hash", 
                "Destination hash must be exactly 64 hexadecimal characters (0-9, a-f).\n\n"
                "You can use either the short or full hash from the recipient."
            )
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Transfer starting...")
        
        # Add to history table
        row = self.transfers_table.rowCount()
        self.transfers_table.insertRow(row)
        self.transfers_table.setItem(row, 0, QTableWidgetItem(Path(file_path).name))
        self.transfers_table.setItem(row, 1, QTableWidgetItem(destination[:16] + "..."))
        self.transfers_table.setItem(row, 2, QTableWidgetItem("0%"))
        self.transfers_table.setItem(row, 3, QTableWidgetItem("Sending..."))
        
        self.transfer_thread = FileTransferThread(
            self.file_transfer_manager,
            file_path,
            destination
        )
        self.transfer_thread.progress_updated.connect(
            lambda cur, tot, pct: self._on_progress(cur, tot, pct, row)
        )
        self.transfer_thread.transfer_complete.connect(
            lambda fp: self._on_complete(fp, row)
        )
        self.transfer_thread.transfer_failed.connect(
            lambda err, fp: self._on_failed(err, fp, row)
        )
        self.transfer_thread.start()
    
    def _on_progress(self, current, total, percentage, row):
        """Update progress bar and table."""
        self.progress_bar.setValue(percentage)
        mb_current = current / (1024 * 1024)
        mb_total = total / (1024 * 1024)
        self.status_label.setText(f"Transferring: {mb_current:.1f} MB / {mb_total:.1f} MB ({percentage}%)")
        
        # Update table
        if row < self.transfers_table.rowCount():
            self.transfers_table.setItem(row, 2, QTableWidgetItem(f"{percentage}%"))
    
    def _on_complete(self, file_path, row):
        """Handle completion."""
        self.status_label.setText("✓ Transfer complete!")
        self.progress_bar.setValue(100)
        if row < self.transfers_table.rowCount():
            self.transfers_table.setItem(row, 3, QTableWidgetItem("Completed"))
        QMessageBox.information(self, "Success", f"File '{Path(file_path).name}' transferred successfully!")
    
    def _on_failed(self, error, file_path, row):
        """Handle failure."""
        self.status_label.setText(f"✗ Transfer failed: {error}")
        if row < self.transfers_table.rowCount():
            self.transfers_table.setItem(row, 3, QTableWidgetItem("Failed"))
        QMessageBox.critical(self, "Transfer Failed", f"Error sending {Path(file_path).name}:\n{error}")
