"""Reticulum node manager with file transfer destination."""

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
            
            # Create dedicated file transfer destination for receiving
            self.file_destination = RNS.Destination(
                self.identity,
                RNS.Destination.IN,
                RNS.Destination.SINGLE,
                "reticulum-meshv",
                "filetransfer"
            )
            
            # Accept all incoming resources (for file transfers)
            self.file_destination.set_resource_strategy(RNS.Destination.ACCEPT_ALL)
            
            # Register resource handler
            self.file_destination.set_resource_concluded_callback(self._resource_concluded)
            
            RNS.log(f"File transfer destination ready: {self.file_destination.hash.hex()[:12]}...")
            
            h_bytes = len(getattr(self.identity, 'hash', b'')) if self.identity else 0
            RNS.log(f"Identity ready. hash bytes={h_bytes}")
            RNS.log(f"Reticulum Mesh node ready. Identity: {self.get_short_identity_hash()}")
        except Exception as e:
            RNS.log(f"Failed to initialize Reticulum: {e}")
            self.reticulum = None
            self.identity = None
            self.file_destination = None
    
    def _resource_concluded(self, resource):
        """Called when an incoming resource (file) is complete."""
        try:
            if resource.status == RNS.Resource.COMPLETE:
                # Save the received file
                filename = getattr(resource, 'filename', None) or f"received_{resource.hash.hex()[:8]}.bin"
                save_path = Path.home() / "Downloads" / "ReticulumMesh" / filename
                save_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(save_path, "wb") as f:
                    f.write(resource.data)
                
                RNS.log(f"Received file saved to: {save_path}")
        except Exception as e:
            RNS.log(f"Error saving received file: {e}")
    
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
