"""Reticulum node manager."""

import RNS
import LXMF
from pathlib import Path

class ReticulumNode:
    """Manages Reticulum network connectivity."""
    
    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            self.reticulum = RNS.Reticulum(configdir=str(self.config_dir))
            self.identity = self._create_identity()
            RNS.log(f"Node ready: {self.identity.hash.hex()[:12]}...")
        except Exception as e:
            RNS.log(f"Failed to initialize Reticulum: {e}")
            self.reticulum = None
            self.identity = None
    
    def _create_identity(self) -> RNS.Identity:
        """Create or load identity."""
        identity_path = self.config_dir / "identity.key"
        
        if identity_path.exists():
            identity = RNS.Identity.from_file(str(identity_path))
        else:
            identity = RNS.Identity()
            identity.to_file(str(identity_path))
        
        return identity
    
    def get_identity_hash(self) -> str:
        """Get identity hash."""
        return self.identity.hash.hex() if self.identity else ""
    
    def is_connected(self) -> bool:
        """Check connection status."""
        return self.reticulum is not None
