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
            # Initialize Reticulum using standard config (for interfaces, shared with rnsd)
            self.reticulum = RNS.Reticulum(configdir=str(self.rns_config_dir))
            
            # Load or create our own persistent identity for this app
            # This keeps app identity separate from Reticulum's internal identity
            self.identity = self._load_or_create_identity()
            
            RNS.log(f"Reticulum Mesh node ready. Identity: {self.get_short_identity_hash()}")
        except Exception as e:
            RNS.log(f"Failed to initialize Reticulum: {e}")
            self.reticulum = None
            self.identity = None
    
    def _load_or_create_identity(self) -> RNS.Identity:
        """Load existing identity or create and save a new persistent one."""
        identity_path = self.app_config_dir / "identity.key"
        
        if identity_path.exists():
            try:
                identity = RNS.Identity.from_file(str(identity_path))
                RNS.log(f"Loaded existing identity from {identity_path}")
                return identity
            except Exception as e:
                RNS.log(f"Failed to load identity, creating new one: {e}")
        
        # Create new identity
        identity = RNS.Identity()
        identity.to_file(str(identity_path))
        RNS.log(f"Created new identity and saved to {identity_path}")
        return identity
    
    def get_identity_hash(self) -> str:
        """Get full identity hash as hex string."""
        return self.identity.hash.hex() if self.identity else ""
    
    def get_short_identity_hash(self, length: int = 16) -> str:
        """Get shortened identity hash for display."""
        full = self.get_identity_hash()
        if not full:
            return "N/A"
        return f"{full[:length]}...{full[-4:]}" if len(full) > length + 4 else full
    
    def is_connected(self) -> bool:
        """Check connection status."""
        return self.reticulum is not None
    
    def get_identity(self) -> RNS.Identity:
        """Return the app identity object."""
        return self.identity
