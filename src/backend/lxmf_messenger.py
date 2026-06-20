"""LXMF-based messaging with file attachment support."""

import time
import signal
import threading
import base64
from pathlib import Path
from typing import Optional, Callable
import RNS
import LXMF


def create_lxmf_router(identity, storagepath, propagation_cost=0):
    if threading.current_thread() != threading.main_thread():
        original_signal = signal.signal
        try:
            signal.signal = lambda s, h: None
            return LXMF.LXMRouter(
                identity=identity,
                storagepath=storagepath,
                propagation_cost=propagation_cost,
            )
        finally:
            signal.signal = original_signal
    else:
        return LXMF.LXMRouter(
            identity=identity,
            storagepath=storagepath,
            propagation_cost=propagation_cost,
        )


class LXMFMessenger:
    def __init__(self, identity: RNS.Identity, storage_dir: str, display_name: str = "Reticulum Mesh User"):
        self.identity = identity
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.display_name = display_name

        self.router = create_lxmf_router(
            identity=identity,
            storagepath=str(self.storage_dir),
        )

        self.delivery_dest = self.router.register_delivery_identity(
            identity, display_name=display_name
        )
        self.delivery_dest.set_proof_strategy(RNS.Destination.PROVE_ALL)
        self.router.register_delivery_callback(self._on_message)

        print(f"[LXMF] Delivery destination hash: {self.delivery_dest.hash.hex()}")
        print(f"[LXMF] Identity hash: {identity.hash.hex()}")

        self.message_callback: Optional[Callable] = None
        self.conversations: dict[str, list] = {}

        # Message history persistence
        self.history_dir = self.storage_dir / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self._load_history()

    def _history_path(self, peer_hash: str) -> Path:
        safe = peer_hash.replace("/", "_").replace("\\", "_")
        return self.history_dir / f"{safe}.json"

    def _load_history(self):
        for f in self.history_dir.glob("*.json"):
            try:
                peer_hash = f.stem
                data = f.read_text()
                import json
                msgs = json.loads(data)
                if isinstance(msgs, list):
                    self.conversations[peer_hash] = msgs
            except:
                pass

    def _save_history(self, peer_hash: str):
        try:
            import json
            msgs = self.conversations.get(peer_hash, [])
            self._history_path(peer_hash).write_text(json.dumps(msgs, indent=2))
        except:
            pass

    def set_display_name(self, name: str):
        self.display_name = name
        try:
            if self.delivery_dest:
                self.delivery_dest.display_name = name
        except:
            pass

    def _on_message(self, lxmessage: LXMF.LXMessage):
        try:
            source_hash = ""
            if lxmessage.source and hasattr(lxmessage.source, 'hash'):
                source_hash = lxmessage.source.hash.hex()
            elif hasattr(lxmessage, 'source_hash') and lxmessage.source_hash:
                source_hash = lxmessage.source_hash.hex() if isinstance(lxmessage.source_hash, bytes) else str(lxmessage.source_hash)

            content = ""
            if lxmessage.content:
                content = lxmessage.content.decode("utf-8", errors="replace")
            elif hasattr(lxmessage, 'content_as_string'):
                try:
                    content = lxmessage.content_as_string()
                except:
                    pass

            title = ""
            if lxmessage.title:
                try:
                    title = lxmessage.title.decode("utf-8", errors="replace") if isinstance(lxmessage.title, bytes) else str(lxmessage.title)
                except:
                    pass

            timestamp = getattr(lxmessage, "timestamp", None) or time.time()

            # Check for file attachments
            file_attachments = []
            try:
                fields = lxmessage.get_fields()
                if LXMF.FIELD_FILE_ATTACHMENTS in fields:
                    for att in fields[LXMF.FIELD_FILE_ATTACHMENTS]:
                        if isinstance(att, (list, tuple)) and len(att) >= 2:
                            fname = att[0]
                            fdata = att[1]
                            if isinstance(fdata, (bytes, bytearray)):
                                file_attachments.append({
                                    "name": fname if isinstance(fname, str) else fname.decode("utf-8", errors="replace"),
                                    "size": len(fdata),
                                    "data": bytes(fdata),
                                })
                                print(f"[LXMF] File attachment: {fname} ({len(fdata)} bytes)")
            except:
                pass

            print(f"[LXMF] Received message from {source_hash[:16]}...: {content[:50]}")

            msg_data = {
                "sender": source_hash,
                "content": content,
                "title": title,
                "timestamp": timestamp,
                "is_outgoing": False,
                "file_attachments": [{"name": a["name"], "size": a["size"]} for a in file_attachments],
            }

            if source_hash not in self.conversations:
                self.conversations[source_hash] = []
            self.conversations[source_hash].append(msg_data)
            self._save_history(source_hash)

            # Save received files to downloads
            if file_attachments:
                import os
                for att in file_attachments:
                    downloads = Path.home() / "Downloads" / "RMESHV"
                    downloads.mkdir(parents=True, exist_ok=True)
                    fpath = downloads / att["name"]
                    with open(fpath, "wb") as f:
                        f.write(att["data"])
                    print(f"[LXMF] Saved file: {fpath}")

            if self.message_callback:
                self.message_callback(source_hash, content, title, timestamp)

        except Exception as e:
            print(f"[LXMF] Error handling message: {e}")
            import traceback
            traceback.print_exc()

    def send_message(self, destination_hash: str, text: str, title: str = "", file_path: str = None) -> bool:
        try:
            dest_bytes = bytes.fromhex(destination_hash)

            # Try to recall the remote identity
            remote_identity = RNS.Identity.recall(dest_bytes)
            if not remote_identity:
                # Try recalling from identity hash
                remote_identity = RNS.Identity.recall(dest_bytes, from_identity_hash=True)
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

            # Request path if not known
            if not RNS.Transport.has_path(dest.hash):
                print(f"[LXMF] Requesting path to {destination_hash[:16]}...")
                RNS.Transport.request_path(dest.hash)

            # Build fields with file attachment if provided
            fields = {}
            if file_path:
                import os
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                fname = os.path.basename(file_path)
                fields[LXMF.FIELD_FILE_ATTACHMENTS] = [(fname, file_data)]
                if not text:
                    text = f"[File: {fname}]"
                print(f"[LXMF] Attaching file: {fname} ({len(file_data)} bytes)")

            message = LXMF.LXMessage(
                dest,
                self.delivery_dest,
                content=text.encode("utf-8") if isinstance(text, str) else text,
                title=title.encode("utf-8") if title else b"",
                fields=fields if fields else None,
            )

            # Use DIRECT method for reliable delivery (link-based)
            message.desired_method = LXMF.LXMessage.DIRECT

            self.router.handle_outbound(message)
            print(f"[LXMF] Sent message to {destination_hash[:16]}...: {text[:50]} (method={message.desired_method})")
            if file_path:
                import os
                print(f"[LXMF] File attached: {os.path.basename(file_path)} ({os.path.getsize(file_path)} bytes)")

            conv_id = destination_hash
            if conv_id not in self.conversations:
                self.conversations[conv_id] = []
            msg_entry = {
                "sender": self.identity.hash.hex(),
                "content": text,
                "title": title,
                "timestamp": time.time(),
                "is_outgoing": True,
            }
            if file_path:
                import os
                msg_entry["file_attachments"] = [{"name": os.path.basename(file_path), "size": os.path.getsize(file_path)}]
            self.conversations[conv_id].append(msg_entry)
            self._save_history(conv_id)
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

    def get_delivery_hash(self) -> str:
        if self.delivery_dest:
            return self.delivery_dest.hash.hex()
        return ""

    def announce(self, app_data: str = "") -> bool:
        try:
            name = app_data if app_data else self.display_name
            if self.delivery_dest:
                self.delivery_dest.display_name = name
            if self.router:
                self.router.announce(destination_hash=self.delivery_dest.hash)
                print(f"[LXMF] Announced as: {name} (hash: {self.delivery_dest.hash.hex()[:16]}...)")
                return True
        except Exception as e:
            print(f"[LXMF] Announce error: {e}")
        return False
