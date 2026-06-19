"""Telephony manager using LXST audio codecs and Reticulum links for signalling."""

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

    SIGNAL_CALL_INIT = 0x01
    SIGNAL_CALL_ACCEPT = 0x02
    SIGNAL_CALL_REJECT = 0x03
    SIGNAL_CALL_END = 0x04
    SIGNAL_AUDIO_FRAME = 0x10

    def __init__(self, identity: RNS.Identity):
        self.identity = identity
        self.state = self.CALL_STATE_IDLE
        self.current_call: Optional[dict] = None
        self.call_history: list = []
        self._state_callback: Optional[Callable] = None
        self._ringtone_callback: Optional[Callable] = None
        self._lock = threading.Lock()
        self._link: Optional[RNS.Link] = None
        self._running = False

        self._setup_destination()

    def _setup_destination(self):
        try:
            self.call_dest = RNS.Destination(
                self.identity,
                RNS.Destination.IN,
                RNS.Destination.SINGLE,
                "reticulum-meshv",
                "telephony"
            )
            self.call_dest.set_link_established_callback(self._on_incoming_link)
        except Exception as e:
            print(f"[Telephony] Setup error: {e}")
            self.call_dest = None

    def _on_incoming_link(self, link: RNS.Link):
        try:
            peer_hash = link.remote_identity.hash.hex() if link.remote_identity else "unknown"
            with self._lock:
                self.current_call = {
                    "peer_hash": peer_hash,
                    "direction": "incoming",
                    "started": time.time(),
                }
                self.state = self.CALL_STATE_RINGING
                self._link = link

            link.set_link_closed_callback(self._on_link_closed)

            if self._ringtone_callback:
                self._ringtone_callback(peer_hash)
            if self._state_callback:
                self._state_callback(self.state, self.current_call)

            link.register_resource(self._on_resource)
            link.set_packet_callback(self._on_packet)

        except Exception as e:
            print(f"[Telephony] Incoming link error: {e}")

    def _on_packet(self, data, packet):
        pass

    def _on_resource(self, resource):
        pass

    def _on_link_closed(self, link):
        with self._lock:
            if self.state in (self.CALL_STATE_ACTIVE, self.CALL_STATE_RINGING, self.CALL_STATE_CONNECTING):
                self._end_call_locked()

    def initiate_call(self, destination_hash: str) -> bool:
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
                "reticulum-meshv",
                "telephony"
            )

            with self._lock:
                self.current_call = {
                    "peer_hash": destination_hash,
                    "direction": "outgoing",
                    "started": time.time(),
                }
                self.state = self.CALL_STATE_CONNECTING

            if self._state_callback:
                self._state_callback(self.state, self.current_call)

            link = RNS.Link.establish(dest)
            if link:
                with self._lock:
                    self._link = link
                    self.state = self.CALL_STATE_ACTIVE
                link.set_link_closed_callback(self._on_link_closed)
                if self._state_callback:
                    self._state_callback(self.state, self.current_call)
                return True

            with self._lock:
                self.state = self.CALL_STATE_IDLE
                self.current_call = None
            return False

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
        if self._link:
            try:
                self._link.teardown()
            except:
                pass
            self._link = None
        self.state = self.CALL_STATE_IDLE
        self.current_call = None
        if self._state_callback:
            self._state_callback(self.state, None)

    def send_audio_frame(self, frame: bytes) -> bool:
        with self._lock:
            if self.state != self.CALL_STATE_ACTIVE or not self._link:
                return False
            try:
                self._link.send(frame)
                return True
            except:
                return False

    def get_call_state(self) -> str:
        return self.state

    def get_call_history(self) -> list:
        return list(self.call_history)

    def on_state_change(self, callback: Callable):
        self._state_callback = callback

    def on_ringtone(self, callback: Callable):
        self._ringtone_callback = callback

    def announce(self) -> bool:
        try:
            if self.call_dest:
                self.call_dest.announce()
                return True
        except:
            pass
        return False
