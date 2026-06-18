"""Reticulum node manager - made resilient to bad config."""

import RNS
from pathlib import Path
import time


class ReticulumNode:
    def __init__(self, rns_config_dir: str, app_config_dir: str):
        self.rns_config_dir = Path(rns_config_dir)
        self.app_config_dir = Path(app_config_dir)

        self.rns_config_dir.mkdir(parents=True, exist_ok=True)
        self.app_config_dir.mkdir(parents=True, exist_ok=True)

        self.discovered_peers = {}
        self.reticulum = None
        self.identity = None
        self.file_destination = None

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

            # Register announcement handler (best effort)
            try:
                RNS.Transport.register_announce_handler(self._announce_received)
            except Exception:
                pass

            RNS.log("Reticulum Mesh node ready. Identity: " + self.get_short_identity_hash())

        except Exception as e:
            # Do NOT crash the whole application.
            # Log the error so user sees it, but let the GUI start.
            try:
                RNS.log(f"Reticulum failed to start (bad config?). Error: {e}")
            except:
                print(f"Reticulum failed to start: {e}")

            self.reticulum = None
            self.identity = None
            self.file_destination = None

    def announce_myself(self):
        if self.file_destination:
            try:
                self.file_destination.announce()
                return True
            except Exception:
                return False
        return False

    def _announce_received(self, destination_hash, announced_identity, app_data):
        try:
            hash_hex = destination_hash.hex()
            if announced_identity:
                self.discovered_peers[hash_hex] = {
                    'name': announced_identity.hash.hex()[:12],
                    'last_seen': time.time()
                }
        except Exception:
            pass

    def get_discovered_peers(self):
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
