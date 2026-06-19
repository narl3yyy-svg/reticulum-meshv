"""LXST-based telephony (voice calls) manager."""

import time
import struct
import threading
from pathlib import Path
from typing import Optional, Callable
import RNS
import LXST


class TelephonyManager:
    CALL_STATE_IDLE = "idle"
    CALL_STATE_RINGING = "ringing"
    CALL_STATE_CONNECTING = "connecting"
    CALL_STATE_ACTIVE = "active"
    CALL_STATE_ENDED = "ended"

    def __init__(self, identity: RNS.Identity):
        self.identity = identity
        self.state = self.CALL_STATE_IDLE
        self.current_call: Optional[dict] = None
        self.call_history: list = []
        self._state_callback: Optional[Callable] = None
        self._audio_callback: Optional[Callable] = None
        self._ringtone_callback: Optional[Callable] = None
        self._lock = threading.Lock()

        self._setup_lxst()

    def _setup_lxst(self):
        try:
            self.lxst_identity = LXST.LXSTIdentity(self.identity)
            self.lxst_router = LXST.LXSTRouter(self.lxst_identity)
            self.lxst_dest = LXST.LXSTDestination(
                self.identity,
                LXST.LXSTDestination.IN,
                LXST.LXSTDestination.SINGLE,
                "reticulum-meshv",
                "telephony"
            )
            self.lxst_router.register_call_handler(self._on_incoming_call)
        except Exception as e:
            print(f"[Telephony] LXST init error: {e}")
            self.lxst_identity = None
            self.lxst_router = None
            self.lxst_dest = None

    def _on_incoming_call(self, call):
        try:
            with self._lock:
                caller_hash = call.source.hash.hex() if call.source else "unknown"
                self.current_call = {
                    "peer_hash": caller_hash,
                    "direction": "incoming",
                    "started": time.time(),
                }
                self.state = self.CALL_STATE_RINGING

            if self._ringtone_callback:
                self._ringtone_callback(caller_hash)

            if self._state_callback:
                self._state_callback(self.state, self.current_call)

        except Exception as e:
            print(f"[Telephony] Incoming call error: {e}")

    def initiate_call(self, destination_hash: str) -> bool:
        try:
            dest_bytes = bytes.fromhex(destination_hash)
            remote_id = RNS.Identity.recall(dest_bytes)

            with self._lock:
                self.current_call = {
                    "peer_hash": destination_hash,
                    "direction": "outgoing",
                    "started": time.time(),
                }
                self.state = self.CALL_STATE_CONNECTING

            if self.lxst_router:
                call = self.lxst_router.initiate_call(remote_id)
                with self._lock:
                    self.state = self.CALL_STATE_ACTIVE

            if self._state_callback:
                self._state_callback(self.state, self.current_call)
            return True

        except Exception as e:
            print(f"[Telephony] Call initiation error: {e}")
            with self._lock:
                self.state = self.CALL_STATE_IDLE
                self.current_call = None
            return False

    def accept_call(self) -> bool:
        with self._lock:
            if self.state != self.CALL_STATE_RINGING:
                return False
            self.state = self.CALL_STATE_ACTIVE

        if self._state_callback:
            self._state_callback(self.state, self.current_call)
        return True

    def reject_call(self) -> bool:
        with self._lock:
            if self.state != self.CALL_STATE_RINGING:
                return False
            self._end_call_locked()
        return True

    def end_call(self):
        with self._lock:
            self._end_call_locked()

    def _end_call_locked(self):
        if self.current_call:
            self.current_call["ended"] = time.time()
            self.current_call["duration"] = time.time() - self.current_call["started"]
            self.call_history.append(self.current_call)
        self.state = self.CALL_STATE_IDLE
        self.current_call = None

        if self._state_callback:
            self._state_callback(self.state, None)

    def send_audio_frame(self, frame: bytes) -> bool:
        if self.state != self.CALL_STATE_ACTIVE or not self.current_call:
            return False
        try:
            dest_hash = self.current_call["peer_hash"]
            dest_bytes = bytes.fromhex(dest_hash)
            remote_id = RNS.Identity.recall(dest_bytes)
            if remote_id:
                link = RNS.Link.establish(remote_id)
                link.send(frame)
                return True
        except:
            pass
        return False

    def get_call_state(self) -> str:
        return self.state

    def get_call_history(self) -> list:
        return list(self.call_history)

    def on_state_change(self, callback: Callable):
        self._state_callback = callback

    def on_audio_frame(self, callback: Callable):
        self._audio_callback = callback

    def on_ringtone(self, callback: Callable):
        self._ringtone_callback = callback

    def announce(self) -> bool:
        try:
            if self.lxst_dest:
                self.lxst_dest.announce()
                return True
        except:
            pass
        return False
