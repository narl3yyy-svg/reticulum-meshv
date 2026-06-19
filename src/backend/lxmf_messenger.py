"""LXMF-based messaging using correct LXMF library API."""

import time
from pathlib import Path
from typing import Optional, Callable
import RNS
import LXMF


class LXMFMessenger:
    def __init__(self, identity: RNS.Identity, storage_dir: str, display_name: str = "Reticulum Mesh User"):
        self.identity = identity
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.display_name = display_name

        self.router = LXMF.LXMRouter(
            identity=identity,
            storagepath=str(self.storage_dir)
        )

        self.delivery_dest = self.router.register_delivery_identity(
            identity, display_name=display_name
        )
        self.delivery_dest.set_proof_strategy(RNS.Destination.PROVE_ALL)
        self.router.register_delivery_callback(self._on_message)

        self.message_callback: Optional[Callable] = None
        self.conversations: dict[str, list] = {}

    def set_display_name(self, name: str):
        self.display_name = name
        try:
            if self.delivery_dest:
                self.delivery_dest.display_name = name
        except:
            pass

    def _on_message(self, lxmessage: LXMF.LXMessage):
        try:
            source_hash = lxmessage.source.hash.hex() if lxmessage.source else "unknown"
            content = lxmessage.content.decode("utf-8", errors="replace") if lxmessage.content else ""
            title = lxmessage.title.decode("utf-8", errors="replace") if lxmessage.title else ""
            timestamp = getattr(lxmessage, "timestamp", time.time())

            msg_data = {
                "sender": source_hash,
                "content": content,
                "title": title,
                "timestamp": timestamp,
                "is_outgoing": False,
            }

            if source_hash not in self.conversations:
                self.conversations[source_hash] = []
            self.conversations[source_hash].append(msg_data)

            if self.message_callback:
                self.message_callback(source_hash, content, title, timestamp)

        except Exception as e:
            print(f"[LXMF] Error handling message: {e}")

    def send_message(self, destination_hash: str, text: str, title: str = "") -> bool:
        try:
            dest_bytes = bytes.fromhex(destination_hash)
            remote_identity = RNS.Identity.recall(dest_bytes)
            if not remote_identity:
                remote_identity = RNS.Identity()
                remote_identity.hash = dest_bytes

            dest = RNS.Destination(
                remote_identity,
                RNS.Destination.OUT,
                RNS.Destination.SINGLE,
                "lxmf",
                "delivery"
            )

            message = LXMF.LXMessage(
                dest,
                self.delivery_dest,
                content=text.encode("utf-8") if isinstance(text, str) else text,
                title=title.encode("utf-8") if title else b"",
            )

            self.router.handle_outbound(message)

            conv_id = destination_hash
            if conv_id not in self.conversations:
                self.conversations[conv_id] = []
            self.conversations[conv_id].append({
                "sender": self.identity.hash.hex(),
                "content": text,
                "title": title,
                "timestamp": time.time(),
                "is_outgoing": True,
            })
            return True

        except Exception as e:
            print(f"[LXMF] Send error: {e}")
            return False

    def get_conversations(self) -> dict:
        return dict(self.conversations)

    def get_conversation(self, peer_hash: str) -> list:
        return self.conversations.get(peer_hash, [])

    def set_message_callback(self, callback: Callable):
        self.message_callback = callback

    def announce(self, app_data: str = "") -> bool:
        try:
            name = app_data if app_data else self.display_name
            if self.delivery_dest:
                self.delivery_dest.display_name = name
            if self.router:
                self.router.announce(destination_hash=self.delivery_dest.hash)
                print(f"[LXMF] Announced as: {name}")
                return True
        except Exception as e:
            print(f"[LXMF] Announce error: {e}")
        return False
