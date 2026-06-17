"""File transfer widget."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QFileDialog, QProgressBar, QLabel,
    QTableWidget, QTableWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
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
        self.transfer_thread = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title = QLabel("Large File Transfers")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Unlimited size support via chunked RNS transfers")
        layout.addWidget(subtitle)
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select file...")
        self.file_path_input.setReadOnly(True)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_file)
        
        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)
        
        # Destination
        dest_layout = QHBoxLayout()
        dest_label = QLabel("Destination Hash:")
        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("Enter destination hash...")
        dest_layout.addWidget(dest_label, 0)
        dest_layout.addWidget(self.dest_input, 1)
        layout.addLayout(dest_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # Send button
        send_btn = QPushButton("Send File")
        send_btn.setMinimumHeight(40)
        send_btn.clicked.connect(self._send_file)
        layout.addWidget(send_btn)
        
        # Recent transfers table
        layout.addWidget(QLabel("Recent Transfers"))
        self.transfers_table = QTableWidget()
        self.transfers_table.setColumnCount(4)
        self.transfers_table.setHorizontalHeaderLabels(
            ["File", "Destination", "Progress", "Status"]
        )
        self.transfers_table.setMaximumHeight(200)
        layout.addWidget(self.transfers_table)
        
        layout.addStretch()
    
    def _browse_file(self):
        """Browse for file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select file to send")
        if file_path:
            self.file_path_input.setText(file_path)
    
    def _send_file(self):
        """Send selected file."""
        file_path = self.file_path_input.text().strip()
        destination = self.dest_input.text().strip()
        
        if not file_path:
            QMessageBox.warning(self, "Error", "Please select a file")
            return
        
        if not destination:
            QMessageBox.warning(self, "Error", "Please enter destination hash")
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Transfer starting...")
        
        self.transfer_thread = FileTransferThread(
            self.file_transfer_manager,
            file_path,
            destination
        )
        self.transfer_thread.progress_updated.connect(self._on_progress)
        self.transfer_thread.transfer_complete.connect(self._on_complete)
        self.transfer_thread.transfer_failed.connect(self._on_failed)
        self.transfer_thread.start()
    
    def _on_progress(self, current, total, percentage):
        """Update progress."""
        self.progress_bar.setValue(percentage)
        mb_current = current / (1024*1024)
        mb_total = total / (1024*1024)
        self.status_label.setText(f"Transferring: {mb_current:.1f}MB / {mb_total:.1f}MB ({percentage}%)")
    
    def _on_complete(self, file_path):
        """Handle completion."""
        self.status_label.setText("✓ Transfer complete!")
        self.progress_bar.setValue(100)
        QMessageBox.information(self, "Success", "File transferred successfully!")
    
    def _on_failed(self, error, file_path):
        """Handle failure."""
        self.status_label.setText(f"✗ Transfer failed: {error}")
        QMessageBox.critical(self, "Transfer Failed", f"Error: {error}")
