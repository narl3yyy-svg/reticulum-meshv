"""LXMF-based messaging with delivery receipts and propagation."""

import time
from pathlib import Path
from typing import Optional, Callable
import RNS
import LXMF


class LXMFMessenger:
    def __init__(self, identity: RNS.Identity, storage_dir: str):
        self.identity = identity
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.router = LXMF.LXMRouter(
            identity=identity,
            storagepath=str(self.storage_dir)
        )
        self.delivery_callback: Optional[Callable] = None
        self.message_callback: Optional[Callable] = None

        self.lxmf_dest = LXMF.LXMFDestination(
            identity,
            LXMF.LXMFDestination.IN,
            LXMF.LXMFDestination.SINGLE,
            "reticulum-meshv",
            "lxmf"
        )
        self.router.register_delivery_identity(
            identity,
            self.lxmf_dest
        )
        self.router.register_message_handler(self._on_message)

        self.conversations: dict[str, list] = {}

    def _on_message(self, message: LXMF.LXMessage):
        try:
            source_hash = message.source.hash.hex() if message.source else "unknown"
            content = message.content.decode("utf-8", errors="replace") if message.content else ""
            timestamp = message.timestamp or time.time()
            title = message.title.decode("utf-8", errors="replace") if message.title else ""

            msg_data = {
                "sender": source_hash,
                "content": content,
                "title": title,
                "timestamp": timestamp,
                "has_delivery": message.has_delivery,
                "wants_receipt": message.wants_receipt,
            }

            conv_id = source_hash
            if conv_id not in self.conversations:
                self.conversations[conv_id] = []
            self.conversations[conv_id].append(msg_data)

            if message.wants_receipt:
                try:
                    receipt = LXMF.LXMessage(
                        destination=LXMF.LXMFDestination(
                            message.source,
                            LXMF.LXMFDestination.OUT,
                            LXMF.LXMFDestination.SINGLE,
                            "reticulum-meshv",
                            "lxmf"
                        ),
                        source=self.identity,
                        content=b"__delivery_receipt__",
                        title=b"Delivery Receipt",
                        receipt=True,
                    )
                    self.router.outbound(receipt)
                except:
                    pass

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

            dest = LXMF.LXMFDestination(
                remote_identity,
                LXMF.LXMFDestination.OUT,
                LXMF.LXMFDestination.SINGLE,
                "reticulum-meshv",
                "lxmf"
            )
            message = LXMF.LXMessage(
                destination=dest,
                source=self.identity,
                content=text.encode("utf-8") if isinstance(text, str) else text,
                title=title.encode("utf-8") if title else b"",
                wants_receipt=True,
            )
            self.router.outbound(message)

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

    def announce(self) -> bool:
        try:
            self.lxmf_dest.announce()
            return True
        except:
            return False

    def get_lxmf_address(self) -> str:
        try:
            return self.lxmf_dest.hash.hex()
        except:
            return ""
