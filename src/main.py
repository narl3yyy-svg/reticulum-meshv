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
        # Reticulum config (interfaces, shared with rnsd daemon)
        self.rns_config_dir = Path.home() / ".reticulum"
        
        # App-specific config for our identity and settings (clean separation)
        self.app_config_dir = Path.home() / ".config" / "reticulum-meshv"
        self.app_config_dir.mkdir(parents=True, exist_ok=True)
        
        self.rns_node = ReticulumNode(
            rns_config_dir=str(self.rns_config_dir),
            app_config_dir=str(self.app_config_dir)
        )
        self.file_transfer_manager = FileTransferManager(self.rns_node.get_identity())
    
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
