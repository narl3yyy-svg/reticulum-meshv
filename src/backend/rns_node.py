"""Reticulum node — identity management and announce handling."""

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

        try:
            self.reticulum = RNS.Reticulum(configdir=str(self.rns_config_dir))
            self.identity = self._load_or_create_identity()

            try:
                RNS.Transport.register_announce_handler(self._announce_received)
            except:
                pass

            print(f"[RNS] Node ready. Identity: {self.get_short_identity_hash()}")

        except Exception as e:
            print(f"[RNS] Init error: {e}")
            self.reticulum = None

    def announce_myself(self, app_data: str = ""):
        return True

    def _announce_received(self, destination_hash, announced_identity, app_data):
        try:
            hash_hex = destination_hash.hex()
            name = app_data.decode("utf-8", errors="replace") if isinstance(app_data, bytes) else (
                str(app_data) if app_data else hash_hex[:12]
            )
            self.discovered_peers[hash_hex] = {
                'name': name,
                'hash_short': hash_hex[:12],
                'app_data': name,
                'last_seen': time.time()
            }
        except:
            pass

    def get_discovered_peers(self):
        return list(self.discovered_peers.items())

    def get_interfaces(self):
        ifaces = []
        try:
            for iface in RNS.Reticulum.interfaces:
                name = str(getattr(iface, "name", "unknown"))
                ifaces.append({
                    "name": name,
                    "type": type(iface).__name__,
                    "online": getattr(iface, "online", False),
                    "bytes_in": getattr(iface, "bytes_in", 0),
                    "bytes_out": getattr(iface, "bytes_out", 0),
                })
        except:
            pass
        return ifaces

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

    def is_connected(self):
        return self.reticulum is not None

    def get_identity(self):
        return self.identity
