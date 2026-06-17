"""Reticulum node manager with improved identity handling."""

import RNS
from pathlib import Path


class ReticulumNode:
    """Manages Reticulum network connectivity and persistent app identity."""
    
    def __init__(self, rns_config_dir: str, app_config_dir: str):
        self.rns_config_dir = Path(rns_config_dir)
        self.app_config_dir = Path(app_config_dir)
        
        self.rns_config_dir.mkdir(parents=True, exist_ok=True)
        self.app_config_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            self.reticulum = RNS.Reticulum(configdir=str(self.rns_config_dir))
            self.identity = self._load_or_create_identity()
            
            h_bytes = len(getattr(self.identity, 'hash', b'')) if self.identity else 0
            h_hex = len(self.get_identity_hash())
            RNS.log(f"Identity ready. hash bytes={h_bytes}, hex chars={h_hex}")
            
            RNS.log(f"Reticulum Mesh node ready. Identity: {self.get_short_identity_hash()}")
        except Exception as e:
            RNS.log(f"Failed to initialize Reticulum: {e}")
            self.reticulum = None
            self.identity = None
    
    def _load_or_create_identity(self) -> RNS.Identity:
        identity_path = self.app_config_dir / "identity.key"
        
        if identity_path.exists():
            try:
                identity = RNS.Identity.from_file(str(identity_path))
                if identity and getattr(identity, 'hash', None):
                    return identity
            except Exception as e:
                RNS.log(f"Failed to load identity file: {e}")
            try:
                identity_path.unlink(missing_ok=True)
            except:
                pass
        
        identity = RNS.Identity()
        identity.to_file(str(identity_path))
        RNS.log(f"Created new identity and saved to {identity_path}")
        return identity
    
    def get_identity_hash(self) -> str:
        if not self.identity or not getattr(self.identity, 'hash', None):
            return ""
        try:
            return self.identity.hash.hex()
        except Exception:
            return ""
    
    def get_short_identity_hash(self, length: int = 16) -> str:
        full = self.get_identity_hash()
        if not full:
            return "N/A"
        if len(full) > length + 4:
            return f"{full[:length]}...{full[-4:]}"
        return full
    
    def is_connected(self) -> bool:
        return self.reticulum is not None
    
    def get_identity(self) -> RNS.Identity:
        return self.identity

    @property
    def hash_length(self) -> int:
        return len(self.get_identity_hash())
