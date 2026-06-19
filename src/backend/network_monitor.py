"""Network topology monitor for peer discovery and visualization."""

import time
import threading
from pathlib import Path
from typing import Optional
import RNS


class NetworkMonitor:
    def __init__(self, reticulum: RNS.Reticulum, identity: RNS.Identity):
        self.reticulum = reticulum
        self.identity = identity
        self.peers: dict[str, dict] = {}
        self.interfaces: dict[str, dict] = {}
        self.paths: dict[str, list] = {}
        self._running = False
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        try:
            RNS.Transport.register_announce_handler(self._on_announce)
        except:
            pass

    def stop(self):
        self._running = False

    def _monitor_loop(self):
        while self._running:
            try:
                self._scan_interfaces()
                self._scan_paths()
            except:
                pass
            time.sleep(5)

    def _scan_interfaces(self):
        with self._lock:
            self.interfaces.clear()
            try:
                for iface in RNS.Reticulum.interfaces:
                    name = str(getattr(iface, "name", "unknown"))
                    self.interfaces[name] = {
                        "type": type(iface).__name__,
                        "online": getattr(iface, "online", False),
                        "bytes_in": getattr(iface, "bytes_in", 0),
                        "bytes_out": getattr(iface, "bytes_out", 0),
                    }
            except:
                pass

    def _scan_paths(self):
        with self._lock:
            try:
                for dest_hash in RNS.Transport.destinations:
                    hops = RNS.Transport.hops_to(dest_hash)
                    if hops is not None:
                        self.paths[dest_hash.hex()] = hops
            except:
                pass

    def _on_announce(self, destination_hash, announced_identity, app_data):
        if not announced_identity:
            return
        hash_hex = destination_hash.hex() if hasattr(destination_hash, 'hex') else destination_hash.hex()
        hash_hex_str = hash_hex
        with self._lock:
            self.peers[hash_hex_str] = {
                "hash": hash_hex_str,
                "hash_short": hash_hex_str[:12],
                "first_seen": self.peers.get(hash_hex_str, {}).get("first_seen", time.time()),
                "last_seen": time.time(),
                "app_data": str(app_data) if app_data else "",
            }

    def get_peers(self) -> list:
        with self._lock:
            return list(self.peers.values())

    def get_interfaces(self) -> dict:
        with self._lock:
            return dict(self.interfaces)

    def get_paths(self) -> dict:
        with self._lock:
            return {k: v for k, v in self.paths.items()}

    def get_network_graph(self) -> dict:
        nodes = []
        edges = []

        with self._lock:
            my_hash = self.identity.hash.hex() if self.identity else ""
            nodes.append({
                "id": my_hash,
                "label": "You",
                "type": "self",
                "group": 0,
            })

            for h, info in self.peers.items():
                nodes.append({
                    "id": h,
                    "label": info.get("app_data", h[:12]),
                    "type": "peer",
                    "group": 1,
                })

            for dest, hops in self.paths.items():
                if dest != my_hash:
                    edges.append({
                        "source": my_hash,
                        "target": dest,
                        "hops": len(hops) if isinstance(hops, list) else hops,
                    })

            for name, info in self.interfaces.items():
                nid = f"iface:{name}"
                nodes.append({
                    "id": nid,
                    "label": name,
                    "type": "interface",
                    "group": 2,
                    "online": info.get("online", False),
                })
                edges.append({
                    "source": my_hash,
                    "target": nid,
                    "hops": 0,
                })

        return {"nodes": nodes, "edges": edges}
