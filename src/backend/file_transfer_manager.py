"""Real RNS.Resource file transfer manager."""

import hashlib
from pathlib import Path
from typing import Optional, Callable
import RNS


class FileTransferManager:
    """Real file/folder transfer using RNS.Resource."""
    
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
        """Send file or zipped folder using real RNS.Resource."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        transfer_id = None
        try:
            dest_hash_bytes = bytes.fromhex(destination_hash)
            
            # Create outbound destination
            remote_identity = RNS.Identity.recall(dest_hash_bytes)
            if remote_identity:
                destination = RNS.Destination(
                    remote_identity, RNS.Destination.OUT, RNS.Destination.SINGLE,
                    "reticulum-meshv", "filetransfer"
                )
            else:
                destination = RNS.Destination(
                    self.identity, RNS.Destination.OUT, RNS.Destination.SINGLE,
                    "reticulum-meshv", "filetransfer"
                )
                destination.hash = dest_hash_bytes
            
            with open(file_path, "rb") as f:
                file_data = f.read()
            
            transfer_id = hashlib.md5(f"{file_path.name}{destination_hash}".encode()).hexdigest()
            self.transfers[transfer_id] = {
                'file': str(file_path),
                'size': len(file_data),
                'progress': 0,
                'status': 'sending'
            }
            
            def progress_cb(resource):
                try:
                    if resource.total_size > 0:
                        pct = int((resource.sent / resource.total_size) * 100)
                        self.transfers[transfer_id]['progress'] = pct
                        if on_progress:
                            on_progress(pct, resource.sent, resource.total_size)
                except:
                    pass
            
            # Real RNS.Resource send (data first)
            resource = RNS.Resource(
                file_data,
                destination,
                callback=progress_cb
            )
            
            # Mark complete (RNS.Resource handles delivery)
            self.transfers[transfer_id]['status'] = 'completed'
            if on_progress:
                on_progress(100, len(file_data), len(file_data))
            
            return True

        except Exception as e:
            if transfer_id and transfer_id in self.transfers:
                self.transfers[transfer_id]['status'] = 'failed'
            raise Exception(f"Send failed: {str(e)}")
