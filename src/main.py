"""Application entry point with text message wiring."""

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

        self.rns_node = None
        self.file_transfer_manager = None
        self.main_window = None

        try:
            self.rns_node = ReticulumNode(
                rns_config_dir=str(self.rns_config_dir),
                app_config_dir=str(self.app_config_dir)
            )

            if self.rns_node:
                self.rns_node.set_text_message_callback(self._on_text_message)

            identity = self.rns_node.get_identity() if self.rns_node else None
            self.file_transfer_manager = FileTransferManager(
                identity,
                downloads_dir=self.downloads_dir,
                rns_node=self.rns_node
            )

        except Exception as e:
            print(f"ReticulumNode creation failed: {e}")
            self.rns_node = None

    def _on_text_message(self, sender_hash: str, text: str):
        """Forward incoming text message to the Messages widget."""
        if self.main_window and hasattr(self.main_window, "messages_widget"):
            try:
                self.main_window.messages_widget.receive_text_message(sender_hash, text)
            except Exception as e:
                print(f"Error delivering text message to UI: {e}")

    def run(self):
        app = QApplication(sys.argv)

        if self.rns_node is None or getattr(self.rns_node, 'reticulum', None) is None:
            QMessageBox.warning(
                None,
                "Reticulum Issue",
                "Reticulum had trouble starting. Messaging may be limited."
            )

        self.main_window = MainWindow(self)

        # Re-wire callback after window exists
        if self.rns_node:
            self.rns_node.set_text_message_callback(self._on_text_message)

        sys.exit(app.exec())


def main():
    application = Application()
    application.run()


if __name__ == "__main__":
    main()
