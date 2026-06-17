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
        self.rns_config_dir = Path.home() / ".reticulum"
        self.app_config_dir = Path.home() / ".config" / "reticulum-meshv"
        self.app_config_dir.mkdir(parents=True, exist_ok=True)
        
        # Downloads folder for received files
        self.downloads_dir = Path.home() / "Downloads" / "ReticulumMesh"
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        
        self.rns_node = ReticulumNode(
            rns_config_dir=str(self.rns_config_dir),
            app_config_dir=str(self.app_config_dir)
        )
        self.file_transfer_manager = FileTransferManager(
            self.rns_node.get_identity(),
            downloads_dir=self.downloads_dir
        )
    
    def run(self):
        app = QApplication(sys.argv)
        window = MainWindow(self)
        sys.exit(app.exec())

def main():
    application = Application()
    application.run()

if __name__ == "__main__":
    main()
