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
            RNS.log(f"Reticulum Mesh node ready. Identity: {self.get_short_identity_hash()}")
        except Exception as e:
            RNS.log(f"Failed to initialize Reticulum: {e}")
            self.reticulum = None
            self.identity = None
    
    def _load_or_create_identity(self) -> RNS.Identity:
        """Load existing identity or create and save a new persistent one.
        
        If the existing file is corrupted or has wrong length, it is deleted and a new one is created.
        """
        identity_path = self.app_config_dir / "identity.key"
        
        if identity_path.exists():
            try:
                identity = RNS.Identity.from_file(str(identity_path))
                
                # Validate that we got a proper 32-byte hash (64 hex chars)
                if identity and len(identity.hash) == 32:
                    RNS.log(f"Loaded existing identity from {identity_path}")
                    return identity
                else:
                    RNS.log("Loaded identity has invalid hash length, creating new one...")
            except Exception as e:
                RNS.log(f"Failed to load identity file: {e}")
            
            # Bad/corrupted identity file -> remove it and create fresh
            try:
                identity_path.unlink()
            except:
                pass
        
        # Create new proper identity
        identity = RNS.Identity()
        identity.to_file(str(identity_path))
        RNS.log(f"Created new identity and saved to {identity_path}")
        return identity
    
    def get_identity_hash(self) -> str:
        """Get full identity hash as 64-character hex string."""
        if not self.identity or not self.identity.hash:
            return ""
        h = self.identity.hash.hex()
        # Ensure we always return 64 chars
        if len(h) != 64:
            RNS.log(f"WARNING: identity hash has wrong length: {len(h)}")
        return h
    
    def get_short_identity_hash(self, length: int = 16) -> str:
        """Get shortened identity hash for display."""
        full = self.get_identity_hash()
        if not full or len(full) != 64:
            return "N/A"
        return f"{full[:length]}...{full[-4:]}"
    
    def is_connected(self) -> bool:
        """Check connection status."""
        return self.reticulum is not None
    
    def get_identity(self) -> RNS.Identity:
        """Return the app identity object."""
        return self.identity
