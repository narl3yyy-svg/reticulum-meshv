"""Application entry point."""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication

from src.backend.rns_node import ReticulumNode
from src.backend.file_transfer_manager import FileTransferManager
from src.ui.main_window import MainWindow

class Application:
    """Main application controller."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".reticulum"
        self.rns_node = ReticulumNode(str(self.config_dir))
        self.file_transfer_manager = FileTransferManager(self.rns_node.identity)
    
    def run(self):
        """Run application."""
        app = QApplication(sys.argv)
        window = MainWindow(self)
        sys.exit(app.exec())

def main():
    """Entry point."""
    application = Application()
    application.run()

if __name__ == "__main__":
    main()
