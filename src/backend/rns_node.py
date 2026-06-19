"""Reticulum node with improved text message handling for mobile interoperability."""

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
        self.pending_text_messages = []   # For incoming small text messages
        self.text_message_callback = None

        self.reticulum = None
        self.identity = None
        self.file_destination = None

        try:
            self.reticulum = RNS.Reticulum(configdir=str(self.rns_config_dir))
            self.identity = self._load_or_create_identity()

            self.file_destination = RNS.Destination(
                self.identity,
                RNS.Destination.IN,
                RNS.Destination.SINGLE,
                "reticulum-meshv",
                "filetransfer"
            )
            self.file_destination.set_proof_strategy(RNS.Destination.PROVE_ALL)

            # Register resource handler
            self.file_destination.set_packet_callback(self._packet_received)
            try:
                RNS.Transport.register_announce_handler(self._announce_received)
            except:
                pass

            RNS.log("Reticulum Mesh node ready. Identity: " + self.get_short_identity_hash())

        except Exception as e:
            try:
                RNS.log(f"Reticulum init error: {e}")
            except:
                print(f"Reticulum init error: {e}")
            self.reticulum = None

    def set_text_message_callback(self, callback):
        """Set a callback function(sender_hash, text) for incoming text messages."""
        self.text_message_callback = callback

    def announce_myself(self, app_data: str = ""):
        if self.file_destination:
            try:
                self.file_destination.announce(app_data.encode("utf-8") if app_data else None)
                return True
            except:
                return False
        return False

    def _announce_received(self, destination_hash, announced_identity, app_data):
        try:
            hash_hex = destination_hash.hex()
            raw = announced_identity.hash.hex() if announced_identity else hash_hex[:12]
            name = app_data.decode("utf-8", errors="replace") if isinstance(app_data, bytes) else (
                str(app_data) if app_data else raw
            )
            self.discovered_peers[hash_hex] = {
                'name': name,
                'hash_short': hash_hex[:12],
                'app_data': name,
                'last_seen': time.time()
            }
        except:
            pass

    def _packet_received(self, packet):
        """Handle incoming packets/resources. Try to treat small ones as text messages."""
        try:
            if packet.data and len(packet.data) < 4096:  # Small payload = likely text
                text = packet.data.decode("utf-8", errors="ignore")
                sender = packet.destination.hash.hex() if hasattr(packet, "destination") else "unknown"

                self.pending_text_messages.append((sender, text))

                if self.text_message_callback:
                    try:
                        self.text_message_callback(sender, text)
                    except:
                        pass
        except:
            pass

    def get_pending_text_messages(self):
        msgs = self.pending_text_messages.copy()
        self.pending_text_messages.clear()
        return msgs

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
