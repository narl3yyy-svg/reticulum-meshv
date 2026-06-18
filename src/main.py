"""Application entry point - made resilient to bad Reticulum config."""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox

from src.backend.rns_node import ReticulumNode
from src.backend.file_transfer_manager import FileTransferManager
from src.ui.main_window import MainWindow


class Application:
    def __init__(self):
        self.rns_config_dir = Path.home() / ".reticulum"
        self.app_config_dir = Path.home() / ".config" / "reticulum-meshv"
        self.app_config_dir.mkdir(parents=True, exist_ok=True)

        self.downloads_dir = Path.home() / "Downloads" / "ReticulumMesh"
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

        # Create ReticulumNode in a way that won't crash the GUI
        try:
            self.rns_node = ReticulumNode(
                rns_config_dir=str(self.rns_config_dir),
                app_config_dir=str(self.app_config_dir)
            )
        except Exception as e:
            # Last-resort safety net
            print(f"Critical error creating ReticulumNode: {e}")
            self.rns_node = None

        # FileTransferManager can handle None rns_node in degraded mode
        try:
            identity = self.rns_node.get_identity() if self.rns_node else None
            self.file_transfer_manager = FileTransferManager(
                identity,
                downloads_dir=self.downloads_dir,
                rns_node=self.rns_node
            )
        except Exception:
            self.file_transfer_manager = None

    def run(self):
        app = QApplication(sys.argv)

        # If Reticulum failed completely, warn the user but still open the app
        if self.rns_node is None or self.rns_node.reticulum is None:
            QMessageBox.warning(
                None,
                "Reticulum Configuration Error",
                "Reticulum could not start due to a problem in ~/.reticulum/config.\n\n"
                "The application will still open. Please go to the Interfaces tab and fix the configuration, then restart."
            )

        window = MainWindow(self)
        sys.exit(app.exec())


def main():
    application = Application()
    application.run()


if __name__ == "__main__":
    main()
