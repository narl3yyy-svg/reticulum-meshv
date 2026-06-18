"""Application entry point with automatic config recovery."""

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

        # Try to start Reticulum, with automatic recovery if config is bad
        try:
            self.rns_node = ReticulumNode(
                rns_config_dir=str(self.rns_config_dir),
                app_config_dir=str(self.app_config_dir)
            )
        except Exception as e:
            print(f"ReticulumNode creation failed: {e}")
            self._recover_from_bad_config()
            # Try one more time after recovery
            try:
                self.rns_node = ReticulumNode(
                    rns_config_dir=str(self.rns_config_dir),
                    app_config_dir=str(self.app_config_dir)
                )
            except Exception as e2:
                print(f"Reticulum still failing after recovery: {e2}")
                self.rns_node = None

        # Create FileTransferManager (degraded mode is ok)
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
        """Backup bad config and create a minimal working one."""
        config_path = self.rns_config_dir / "config"
        if config_path.exists():
            backup_path = config_path.with_suffix(".config.bad")
            try:
                config_path.rename(backup_path)
                print(f"Backed up bad config to {backup_path}")
            except Exception as e:
                print(f"Could not backup bad config: {e}")

        # Create a minimal safe config
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            minimal_config = '''[reticulum]
enable_transport = False
share_instance = Yes

[logging]
loglevel = 4

[interfaces]

    [[AutoInterface]]
    interface_enabled = True
'''
            config_path.write_text(minimal_config)
            print("Created minimal safe config. Reticulum should start now.")
        except Exception as e:
            print(f"Failed to create minimal config: {e}")

    def run(self):
        app = QApplication(sys.argv)

        if self.rns_node is None or getattr(self.rns_node, 'reticulum', None) is None:
            QMessageBox.warning(
                None,
                "Reticulum Had Issues",
                "There was a problem starting Reticulum (likely a bad config).\n\n"
                "The application will still open. Go to the Interfaces tab to review/fix the configuration, then restart."
            )

        window = MainWindow(self)
        sys.exit(app.exec())


def main():
    application = Application()
    application.run()


if __name__ == "__main__":
    main()
