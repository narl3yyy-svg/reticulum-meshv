"""Network topology monitor for peer discovery and visualization."""

import time
import threading
from typing import Optional
import RNS


class AnnounceHandler:
    """RNS announce handler that filters by aspect and forwards to callback."""

    def __init__(self, aspect_filter, callback):
        self.aspect_filter = aspect_filter
        self._callback = callback

    def received_announce(self, destination_hash, announced_identity, app_data, announce_packet_hash=None):
        try:
            self._callback(destination_hash, announced_identity, app_data)
        except Exception as e:
            print(f"[Network] Announce handler error: {e}")


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
        self._announce_handlers = []

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

        for aspect in ["lxmf.delivery", "lxmf.propagation", "lxst.telephony", "nomadnetwork.node"]:
            try:
                handler = AnnounceHandler(aspect, self._on_announce)
                RNS.Transport.register_announce_handler(handler)
                self._announce_handlers.append(handler)
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
                for iface in RNS.Transport.interfaces:
                    name = str(getattr(iface, "name", str(iface)))
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
            self.paths.clear()
            try:
                # Scan known paths from path table
                for dest_hash in RNS.Transport.path_table:
                    hops = RNS.Transport.hops_to(dest_hash)
                    if hops is not None:
                        if hasattr(dest_hash, 'hex'):
                            self.paths[dest_hash.hex()] = hops
                        elif isinstance(dest_hash, bytes):
                            self.paths[dest_hash.hex()] = hops
            except:
                pass
            try:
                # Also scan local destinations
                for dest_hash in RNS.Transport.destinations:
                    hops = RNS.Transport.hops_to(dest_hash)
                    if hops is not None:
                        if hasattr(dest_hash, 'hex'):
                            self.paths[dest_hash.hex()] = hops
                        elif isinstance(dest_hash, bytes):
                            self.paths[dest_hash.hex()] = hops
            except:
                pass

    def _on_announce(self, destination_hash, announced_identity, app_data):
        if not announced_identity:
            return
        hash_hex = destination_hash.hex() if hasattr(destination_hash, 'hex') else str(destination_hash)

        # Decode app_data - LXMF uses msgpack [display_name, stamp_cost, features]
        app_data_str = ""
        if app_data:
            if isinstance(app_data, bytes):
                try:
                    import msgpack
                    unpacked = msgpack.unpackb(app_data, raw=False)
                    if isinstance(unpacked, (list, tuple)) and len(unpacked) >= 1:
                        name = unpacked[0]
                        if isinstance(name, bytes):
                            app_data_str = name.decode("utf-8", errors="replace")
                        elif isinstance(name, str):
                            app_data_str = name
                    else:
                        app_data_str = str(unpacked)
                except:
                    try:
                        app_data_str = app_data.decode("utf-8", errors="replace")
                    except:
                        app_data_str = app_data.hex()[:16]
            else:
                app_data_str = str(app_data)

        with self._lock:
            self.peers[hash_hex] = {
                "hash": hash_hex,
                "hash_short": hash_hex[:12],
                "first_seen": self.peers.get(hash_hex, {}).get("first_seen", time.time()),
                "last_seen": time.time(),
                "app_data": app_data_str,
            }
        print(f"[Network] Announce received from {hash_hex[:16]}... ({app_data_str})")

    def get_peers(self) -> list:
        with self._lock:
            return list(self.peers.values())

    def get_interfaces(self) -> dict:
        with self._lock:
            return dict(self.interfaces)

    def get_paths(self) -> dict:
        with self._lock:
            return {k: v for k, v in self.paths.items()}
