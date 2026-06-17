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
            
            hlen = len(self.identity.hash) if self.identity and self.identity.hash else 0
            RNS.log(f"Identity created. hash bytes length = {hlen}, hex length = {len(self.get_identity_hash())}")
            
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
                if identity and len(getattr(identity, 'hash', b'')) == 32:
                    RNS.log(f"Loaded existing identity from {identity_path}")
                    return identity
                else:
                    RNS.log("Loaded identity invalid or wrong hash length, recreating...")
            except Exception as e:
                RNS.log(f"Failed to load identity: {e}")
            
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
        except:
            return ""
    
    def get_short_identity_hash(self, length: int = 16) -> str:
        full = self.get_identity_hash()
        if not full:
            return "N/A"
        # If we only got 32 chars, still show something usable
        if len(full) == 32:
            return f"{full[:16]}...{full[-4:]}"
        if len(full) > length + 4:
            return f"{full[:length]}...{full[-4:]}"
        return full
    
    def is_connected(self) -> bool:
        return self.reticulum is not None
    
    def get_identity(self) -> RNS.Identity:
        return self.identity
