"""File transfer manager - simulated but saves file on self-send."""

import hashlib
from pathlib import Path
from typing import Optional, Callable
import RNS


class FileTransferManager:
    """File transfer manager (simulated progress + self-send file creation)."""
    
    def __init__(self, identity: RNS.Identity, downloads_dir: Optional[Path] = None, rns_node=None):
        self.identity = identity
        self.rns_node = rns_node
        self.transfers = {}
        
        if downloads_dir:
            self.downloads_dir = Path(downloads_dir)
        else:
            self.downloads_dir = Path.home() / "Downloads" / "ReticulumMesh"
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
    
    def send_file(
        self,
        file_path: str,
        destination_hash: str,
        on_progress: Optional[Callable] = None,
    ):
        """Send file. On self-send, actually copies the file to downloads folder."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        transfer_id = None
        try:
            dest_hash_bytes = bytes.fromhex(destination_hash)
            my_hash = self.identity.hash

            transfer_id = hashlib.md5(f"{file_path.name}{destination_hash}".encode()).hexdigest()
            self.transfers[transfer_id] = {
                'file': str(file_path),
                'size': file_path.stat().st_size,
                'progress': 0,
                'status': 'sending'
            }
            
            total_size = file_path.stat().st_size

            # Simulate progress
            for pct in range(0, 101, 5):
                if on_progress:
                    current = int(total_size * pct / 100)
                    on_progress(pct, current, total_size)
                import time
                time.sleep(0.03)

            # If sending to self, actually save a copy
            if dest_hash_bytes == my_hash:
                dest_filename = f"self_{file_path.name}"
                dest_path = self.downloads_dir / dest_filename
                import shutil
                shutil.copy2(file_path, dest_path)
                RNS.log(f"Self-send: File copied to {dest_path}")
            else:
                RNS.log("Note: Real remote sending not yet active (simulated)")

            self.transfers[transfer_id]['status'] = 'completed'
            if on_progress:
                on_progress(100, total_size, total_size)

            return True

        except Exception as e:
            if transfer_id and transfer_id in self.transfers:
                self.transfers[transfer_id]['status'] = 'failed'
            raise Exception(f"Send failed: {str(e)}")
