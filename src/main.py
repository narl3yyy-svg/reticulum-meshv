"""Application entry point with full feature wiring."""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox

from src.backend.rns_node import ReticulumNode
from src.backend.file_transfer_manager import FileTransferManager
from src.backend.lxmf_messenger import LXMFMessenger
from src.backend.identity_manager import IdentityManager
from src.backend.contact_manager import ContactManager
from src.backend.network_monitor import NetworkMonitor
from src.backend.telephony_manager import TelephonyManager
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
        self.lxmf_messenger = None
        self.identity_manager = None
        self.contact_manager = None
        self.network_monitor = None
        self.telephony_manager = None
        self.main_window = None

        self._init_backend()

    def _init_backend(self):
        try:
            self.rns_node = ReticulumNode(
                rns_config_dir=str(self.rns_config_dir),
                app_config_dir=str(self.app_config_dir)
            )
            if not self.rns_node or not self.rns_node.reticulum:
                print("Reticulum node failed to initialize")
                return

            self.identity_manager = IdentityManager(str(self.app_config_dir))
            self.contact_manager = ContactManager(str(self.app_config_dir))

            identity = self.rns_node.get_identity()
            if identity:
                self.file_transfer_manager = FileTransferManager(
                    identity,
                    downloads_dir=self.downloads_dir,
                    rns_node=self.rns_node
                )

                self.lxmf_messenger = LXMFMessenger(
                    identity,
                    storage_dir=str(self.app_config_dir / "lxmf")
                )
                self.lxmf_messenger.set_message_callback(self._on_lxmf_message)

                self.network_monitor = NetworkMonitor(
                    self.rns_node.reticulum,
                    identity
                )
                self.network_monitor.start()

                self.telephony_manager = TelephonyManager(identity)

            if self.rns_node:
                self.rns_node.set_text_message_callback(self._on_text_message)

        except Exception as e:
            print(f"Backend initialization error: {e}")
            import traceback
            traceback.print_exc()

    def _on_text_message(self, sender_hash: str, text: str):
        if self.main_window and hasattr(self.main_window, "messages_widget"):
            try:
                self.main_window.messages_widget.receive_text_message(sender_hash, text)
            except Exception as e:
                print(f"Error delivering text message to UI: {e}")

    def _on_lxmf_message(self, sender_hash: str, content: str, title: str, timestamp: float):
        self.contact_manager.touch(sender_hash)
        if self.main_window and hasattr(self.main_window, "messages_widget"):
            try:
                self.main_window.messages_widget.receive_lxmf_message(sender_hash, content, title, timestamp)
            except Exception as e:
                print(f"Error delivering LXMF message to UI: {e}")

    def run(self):
        app = QApplication(sys.argv)

        if self.rns_node is None or getattr(self.rns_node, 'reticulum', None) is None:
            QMessageBox.warning(
                None,
                "Reticulum Issue",
                "Reticulum had trouble starting. Some features may be limited."
            )

        self.main_window = MainWindow(self)

        if self.rns_node:
            self.rns_node.set_text_message_callback(self._on_text_message)

        if self.lxmf_messenger:
            self.lxmf_messenger.set_message_callback(self._on_lxmf_message)

        sys.exit(app.exec())


def main():
    application = Application()
    application.run()


if __name__ == "__main__":
    main()
