"""Reticulum node with announcement and peer discovery support."""

import RNS
from pathlib import Path
import time


class ReticulumNode:
    def __init__(self, rns_config_dir: str, app_config_dir: str):
        self.rns_config_dir = Path(rns_config_dir)
        self.app_config_dir = Path(app_config_dir)

        self.rns_config_dir.mkdir(parents=True, exist_ok=True)
        self.app_config_dir.mkdir(parents=True, exist_ok=True)

        self.discovered_peers = {}  # hash -> {'name': str, 'last_seen': float}

        try:
            self.reticulum = RNS.Reticulum(configdir=str(self.rns_config_dir))
            self.identity = self._load_or_create_identity()

            # Main file transfer destination (announceable)
            self.file_destination = RNS.Destination(
                self.identity,
                RNS.Destination.IN,
                RNS.Destination.SINGLE,
                "reticulum-meshv",
                "filetransfer"
            )

            # Register announcement handler for discovery
            RNS.Transport.register_announce_handler(self._announce_received)

            RNS.log("Announcement handler registered")
            RNS.log(f"Reticulum Mesh node ready. Identity: {self.get_short_identity_hash()}")

        except Exception as e:
            RNS.log(f"Failed to initialize Reticulum: {e}")
            self.reticulum = None
            self.identity = None
            self.file_destination = None

    def announce_myself(self):
        """Announce our presence on the network."""
        if self.file_destination:
            self.file_destination.announce()
            RNS.log("Announced presence on the network")
            return True
        return False

    def _announce_received(self, destination_hash, announced_identity, app_data):
        """Called when we receive an announcement."""
        try:
            hash_hex = destination_hash.hex()
            # Only care about our app context or general announcements
            if announced_identity:
                self.discovered_peers[hash_hex] = {
                    'name': announced_identity.hash.hex()[:12],
                    'last_seen': time.time()
                }
                RNS.log(f"Discovered peer: {hash_hex[:12]}...")
        except Exception as e:
            RNS.log(f"Error processing announcement: {e}")

    def get_discovered_peers(self):
        """Return list of recently discovered peers."""
        return list(self.discovered_peers.items())

    def _load_or_create_identity(self):
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

    def get_identity_hash(self):
        if not self.identity or not getattr(self.identity, "hash", None):
            return ""
        try:
            return self.identity.hash.hex()
        except:
            return ""

    def get_short_identity_hash(self, length: int = 16):
        full = self.get_identity_hash()
        if not full:
            return "N/A"
        if len(full) > length + 4:
            return f"{full[:length]}...{full[-4:]}"
        return full

    @property
    def hash_length(self):
        return len(self.get_identity_hash())

    def is_connected(self):
        return self.reticulum is not None

    def get_identity(self):
        return self.identity
