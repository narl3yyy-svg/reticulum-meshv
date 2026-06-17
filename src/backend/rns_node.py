"""Reticulum node manager with safe resource handling."""

import RNS
from pathlib import Path
import zipfile


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
            
            # Create file transfer destination
            self.file_destination = RNS.Destination(
                self.identity,
                RNS.Destination.IN,
                RNS.Destination.SINGLE,
                "reticulum-meshv",
                "filetransfer"
            )
            
            # Try to set resource acceptance (different RNS versions have different APIs)
            try:
                if hasattr(self.file_destination, "set_resource_strategy"):
                    self.file_destination.set_resource_strategy(RNS.Destination.ACCEPT_ALL)
            except Exception:
                pass
            
            # Try to register concluded callback (may not exist in all versions)
            try:
                if hasattr(self.file_destination, "set_resource_concluded_callback"):
                    self.file_destination.set_resource_concluded_callback(self._resource_concluded)
                else:
                    RNS.log("Note: Resource concluded callback not available in this RNS version")
            except Exception as e:
                RNS.log(f"Could not set resource callback: {e}")
            
            RNS.log("File transfer destination ready")
            RNS.log(f"Reticulum Mesh node ready. Identity: {self.get_short_identity_hash()}")
        except Exception as e:
            RNS.log(f"Failed to initialize Reticulum: {e}")
            self.reticulum = None
            self.identity = None
            self.file_destination = None
    
    def _resource_concluded(self, resource):
        """Handle completed incoming resource."""
        try:
            if resource.status != RNS.Resource.COMPLETE:
                return
            
            filename = getattr(resource, 'filename', None) or getattr(resource, 'name', None) or "received_file"
            save_path = self._get_downloads_dir() / filename
            
            with open(save_path, "wb") as f:
                f.write(resource.data)
            
            RNS.log(f"Received file saved: {save_path}")
            
            # Auto-extract zip files (for folder transfers)
            if str(filename).lower().endswith(".zip"):
                try:
                    extract_dir = save_path.with_suffix("")
                    with zipfile.ZipFile(save_path, "r") as zip_ref:
                        zip_ref.extractall(extract_dir)
                    save_path.unlink(missing_ok=True)
                    RNS.log(f"Auto-extracted to: {extract_dir}")
                except Exception as e:
                    RNS.log(f"Auto-extract error: {e}")
        except Exception as e:
            RNS.log(f"Error in resource handler: {e}")
    
    def _get_downloads_dir(self):
        d = Path.home() / "Downloads" / "ReticulumMesh"
        d.mkdir(parents=True, exist_ok=True)
        return d
    
    def _load_or_create_identity(self) -> RNS.Identity:
        identity_path = self.app_config_dir / "identity.key"
        if identity_path.exists():
            try:
                identity = RNS.Identity.from_file(str(identity_path))
                if identity and getattr(identity, "hash", None):
                    return identity
            except:
                pass
            try:
                identity_path.unlink(missing_ok=True)
            except:
                pass
        identity = RNS.Identity()
        identity.to_file(str(identity_path))
        return identity
    
    def get_identity_hash(self) -> str:
        if not self.identity or not getattr(self.identity, "hash", None):
            return ""
        try:
            return self.identity.hash.hex()
        except:
            return ""
    
    def get_short_identity_hash(self, length: int = 16) -> str:
        full = self.get_identity_hash()
        if not full:
            return "N/A"
        if len(full) > length + 4:
            return f"{full[:length]}...{full[-4:]}"
        return full
    
    @property
    def hash_length(self) -> int:
        return len(self.get_identity_hash())
    
    def is_connected(self) -> bool:
        return self.reticulum is not None
    
    def get_identity(self) -> RNS.Identity:
        return self.identity
