"""File transfer manager (stub + ready for real RNS.Resource implementation)."""

import asyncio
import hashlib
from pathlib import Path
from typing import Optional, Callable
import RNS


class FileTransferManager:
    """Manages chunked file transfers over Reticulum."""
    
    CHUNK_SIZE = 65536  # 64KB
    
    def __init__(self, identity: RNS.Identity, downloads_dir: Optional[Path] = None):
        self.identity = identity
        self.transfers = {}
        
        # Where received files will be saved
        if downloads_dir:
            self.downloads_dir = Path(downloads_dir)
            self.downloads_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.downloads_dir = Path.home() / "Downloads" / "ReticulumMesh"
            self.downloads_dir.mkdir(parents=True, exist_ok=True)
    
    async def send_file(
        self,
        file_path: str,
        destination_hash: str,
        on_progress: Optional[Callable] = None,
    ):
        """Send file with progress tracking (currently simulated)."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = file_path.stat().st_size
        file_hash = self._calculate_hash(file_path)
        transfer_id = hashlib.md5(f"{file_path.name}{destination_hash}".encode()).hexdigest()
        
        self.transfers[transfer_id] = {
            'file': str(file_path),
            'size': file_size,
            'hash': file_hash,
            'progress': 0,
            'status': 'sending'
        }
        
        try:
            bytes_sent = 0
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(self.CHUNK_SIZE)
                    if not chunk:
                        break
                    
                    bytes_sent += len(chunk)
                    progress = (bytes_sent / file_size) * 100
                    self.transfers[transfer_id]['progress'] = progress
                    
                    if on_progress:
                        on_progress(progress, bytes_sent, file_size)
                    
                    await asyncio.sleep(0.01)
            
            self.transfers[transfer_id]['status'] = 'completed'
        except Exception as e:
            self.transfers[transfer_id]['status'] = 'failed'
            raise
    
    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate file SHA256."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def get_transfer_status(self, transfer_id: str) -> dict:
        """Get transfer status."""
        return self.transfers.get(transfer_id, {})
