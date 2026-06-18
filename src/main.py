"""Application entry point with robust config recovery."""

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

        try:
            self.rns_node = ReticulumNode(
                rns_config_dir=str(self.rns_config_dir),
                app_config_dir=str(self.app_config_dir)
            )
        except Exception as e:
            print(f"Initial ReticulumNode creation failed: {e}")
            self._recover_from_bad_config()
            try:
                self.rns_node = ReticulumNode(
                    rns_config_dir=str(self.rns_config_dir),
                    app_config_dir=str(self.app_config_dir)
                )
            except Exception as e2:
                print(f"Reticulum still failing after recovery attempt: {e2}")
                self.rns_node = None

        try:
            identity = self.rns_node.get_identity() if self.rns_node else None
            self.file_transfer_manager = FileTransferManager(
                identity,
                downloads_dir=self.downloads_dir,
                rns_node=self.rns_node
            )
        except Exception:
            self.file_transfer_manager = None

    def _recover_from_bad_config(self):
        config_path = self.rns_config_dir / "config"
        if config_path.exists():
            try:
                backup_path = config_path.with_name("config.bad")
                if backup_path.exists():
                    backup_path.unlink()
                config_path.rename(backup_path)
                print(f"Backed up broken config to {backup_path}")
            except Exception as e:
                print(f"Backup failed: {e}")

        # Create a clean, standard minimal config that Reticulum accepts
        try:
            minimal = '''[reticulum]
enable_transport = False
share_instance = Yes

[logging]
loglevel = 4

[interfaces]

    [[AutoInterface]]
    type = AutoInterface
    interface_enabled = True
'''
            config_path.write_text(minimal)
            print("Created clean minimal config with proper 'type' key.")
        except Exception as e:
            print(f"Failed to write minimal config: {e}")

    def run(self):
        app = QApplication(sys.argv)

        if self.rns_node is None or getattr(self.rns_node, 'reticulum', None) is None:
            QMessageBox.warning(
                None,
                "Reticulum Configuration Problem",
                "Reticulum had trouble starting (bad config file).\n\n"
                "The app will still open. Go to the Interfaces tab to fix the configuration, then restart."
            )

        window = MainWindow(self)
        sys.exit(app.exec())


def main():
    application = Application()
    application.run()


if __name__ == "__main__":
    main()
