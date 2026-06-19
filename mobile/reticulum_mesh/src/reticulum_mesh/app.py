"""Reticulum Mesh Mobile App - Self-contained."""

import os
import sys
import time
import threading
import hashlib
from pathlib import Path

BACKEND_AVAILABLE = False
try:
    import RNS
    BACKEND_AVAILABLE = True
except ImportError:
    RNS = None

try:
    import LXMF
except ImportError:
    LXMF = None

from toga import App, MainWindow, Box, Label, Button, ScrollContainer, TextInput
try:
    from toga.style import Pack
    from toga.constants import COLUMN, ROW
except ImportError:
    from toga.style.pack import Pack
    from toga.constants import COLUMN, ROW


def get_timestamp():
    from datetime import datetime
    return datetime.now().strftime("%H:%M")


class MobileReticulumNode:
    def __init__(self):
        self.reticulum = None
        self.identity = None
        self.identity_hash = ""
        self.discovered_peers = {}

        if BACKEND_AVAILABLE:
            self._init_rns()
        else:
            self._init_local()

    def _init_local(self):
        print("[Mobile] Using local-only mode (RNS not available)")
        path = Path.home() / ".config" / "reticulum-mesh-mobile" / "identity_local.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            try:
                self.identity_hash = path.read_text().strip()
                if len(self.identity_hash) == 64:
                    print(f"[Mobile] Loaded local identity: {self.identity_hash[:12]}...")
                    return
            except:
                pass
        self.identity_hash = os.urandom(32).hex()
        try:
            path.write_text(self.identity_hash)
            print(f"[Mobile] Generated local identity: {self.identity_hash[:12]}...")
        except:
            pass

    def _init_rns(self):
        try:
            config_dir = str(Path.home() / ".reticulum")
            self.reticulum = RNS.Reticulum(configdir=config_dir)
            self.identity = self._load_rns_identity()
            self.identity_hash = self.identity.hash.hex() if self.identity else ""

            try:
                RNS.Transport.register_announce_handler(self._on_announce_rns)
            except:
                pass
        except Exception as e:
            import traceback
            print(f"[Mobile] RNS init error: {e}")
            traceback.print_exc()
            print("[Mobile] Falling back to local-only mode")
            self._init_local()

    def _load_rns_identity(self):
        path = Path.home() / ".config" / "reticulum-mesh-mobile" / "identity.key"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            try:
                identity = RNS.Identity.from_file(str(path))
                if identity and identity.hash:
                    return identity
            except:
                pass
            try:
                path.unlink(missing_ok=True)
            except:
                pass
        identity = RNS.Identity()
        identity.to_file(str(path))
        return identity

    def _on_announce_rns(self, destination_hash, announced_identity, app_data):
        if not announced_identity:
            return
        hash_hex = destination_hash.hex() if hasattr(destination_hash, 'hex') else destination_hash
        self.discovered_peers[hash_hex] = {
            "name": announced_identity.hash.hex()[:12] if announced_identity else hash_hex[:12],
            "last_seen": time.time(),
        }

    def get_identity_hash(self):
        return self.identity_hash

    def get_discovered_peers(self):
        return list(self.discovered_peers.items())

    def announce_myself(self):
        if BACKEND_AVAILABLE and self.identity:
            try:
                dest = RNS.Destination(
                    self.identity,
                    RNS.Destination.IN,
                    RNS.Destination.SINGLE,
                    "reticulum-meshv",
                    "announce"
                )
                dest.announce()
                print("[Mobile] announce: OK")
                return True
            except Exception as e:
                print(f"[Mobile] announce failed: {e}")
                import traceback
                traceback.print_exc()
                return False
        print("[Mobile] announce: local-only (no-op)")
        return True

    def send_text(self, destination_hash, text):
        if not BACKEND_AVAILABLE or not self.identity:
            print("[Mobile] send_text: RNS unavailable")
            return False
        try:
            dest_bytes = bytes.fromhex(destination_hash)
            remote_id = RNS.Identity.recall(dest_bytes)
            if not remote_id:
                remote_id = RNS.Identity()
                remote_id.hash = dest_bytes

            if LXMF:
                router = LXMF.LXMRouter(identity=self.identity)
                dest = RNS.Destination(remote_id, RNS.Destination.OUT, RNS.Destination.SINGLE, "lxmf", "delivery")
                msg = LXMF.LXMessage(dest, self.identity, content=text.encode("utf-8"))
                router.handle_outbound(msg)
                return True
            else:
                dest = RNS.Destination(remote_id, RNS.Destination.OUT, RNS.Destination.SINGLE, "reticulum-meshv", "filetransfer")
                RNS.Resource(text.encode("utf-8"), dest)
                return True
        except:
            return False


def make_container():
    c = Box()
    c.style.direction = COLUMN
    c.style.flex = 1
    return c


def make_label(text, size=11, margin_b=6):
    l = Label(text)
    l.style.font_size = size
    l.style.margin_bottom = margin_b
    return l


class MessagesScreen(Box):
    def __init__(self, node):
        super().__init__()
        self.style.direction = COLUMN
        self.style.flex = 1
        self.style.margin = 8

        self.node = node
        self.current_dest = ""

        self.add(make_label("Messages", size=20, margin_b=6))

        dest_row = Box()
        dest_row.style.direction = ROW
        dest_row.style.margin_bottom = 6

        to_lbl = Label("To:")
        to_lbl.style.margin_right = 6
        dest_row.add(to_lbl)

        self.dest_input = TextInput(placeholder="64-char hash")
        self.dest_input.style.flex = 1

        start_btn = Button("Chat", on_press=self.start_chat)
        start_btn.style.width = 70

        dest_row.add(self.dest_input)
        dest_row.add(start_btn)
        self.add(dest_row)

        self.status_label = make_label("Enter a destination hash.")
        self.add(self.status_label)

        self.scroll = ScrollContainer()
        self.scroll.style.flex = 1

        self.chat_box = Box()
        self.chat_box.style.direction = COLUMN
        self.scroll.content = self.chat_box
        self.add(self.scroll)

        input_row = Box()
        input_row.style.direction = ROW
        input_row.style.margin_top = 8

        self.input = TextInput(placeholder="Type a message...")
        self.input.style.flex = 1
        self.input.style.margin_right = 8

        send_btn = Button("Send", on_press=self.send_message)
        send_btn.style.width = 70

        input_row.add(self.input)
        input_row.add(send_btn)
        self.add(input_row)

        self.add_bubble("Announce yourself first for discoverability.", is_sent=False)

    def start_chat(self, widget):
        dest = "".join(c for c in self.dest_input.value.strip() if c in "0123456789abcdefABCDEF").lower()
        if len(dest) == 64:
            self.current_dest = dest
            self.add_bubble(f"Chat started with {dest[:12]}...", is_sent=False)
            self.status_label.text = "Chat active."
        else:
            self.add_bubble(f"Hash must be 64 hex chars, got {len(dest)}.", is_sent=False)

    def add_bubble(self, text, is_sent=True):
        box = Box()
        box.style.margin = 5
        box.style.margin_left = 65 if is_sent else 8
        box.style.margin_right = 8 if is_sent else 65

        lbl = Label(text)
        lbl.style.margin = 8
        lbl.style.margin_bottom = 2
        box.add(lbl)
        box.add(make_label(get_timestamp(), size=10, margin_b=0))
        self.chat_box.add(box)

    def send_message(self, widget):
        if not self.current_dest:
            self.add_bubble("Start a chat first.", is_sent=False)
            return
        text = self.input.value.strip()
        if not text:
            return
        self.add_bubble(text, is_sent=True)
        self.input.value = ""
        sent = self.node.send_text(self.current_dest, text) if self.node else False
        if not sent:
            self.add_bubble("Send failed", is_sent=False)


class ContactsScreen(Box):
    def __init__(self, node):
        super().__init__()
        self.style.direction = COLUMN
        self.style.margin = 10
        self.node = node

        self.add(make_label("Contacts", size=20, margin_b=8))

        announce_btn = Button("Announce Myself", on_press=self.announce)
        self.add(announce_btn)

        self.status = Label("")
        self.add(self.status)

        self.add(make_label("Discovered Peers:", size=14, margin_b=6))
        self.peer_label = make_label("(refresh to see peers)")
        self.add(self.peer_label)

        refresh_btn = Button("Refresh", on_press=self.refresh_peers)
        self.add(refresh_btn)

        self.refresh_peers(None)

    def announce(self, widget):
        if self.node:
            self.status.text = "Announced!" if self.node.announce_myself() else "Failed"

    def refresh_peers(self, widget):
        if not self.node:
            self.peer_label.text = "Reticulum not available"
            return
        peers = self.node.get_discovered_peers()
        self.peer_label.text = "\n".join([f"{h[:12]}..." for h, _ in peers[:5]]) if peers else "No peers discovered"


class NetworkScreen(Box):
    def __init__(self, node):
        super().__init__()
        self.style.direction = COLUMN
        self.style.margin = 10
        self.node = node

        self.add(make_label("Network", size=20, margin_b=8))

        h = self.node.get_identity_hash() if self.node else ""
        label = f"Identity:\n{h[:32]}..." if h else "Identity:\nRNS not available"
        self.add(make_label(label, size=11, margin_b=12))

        refresh_btn = Button("Refresh", on_press=self.refresh_network)
        self.add(refresh_btn)

        self.status = make_label("")
        self.add(self.status)
        self.refresh_network(None)

    def refresh_network(self, widget):
        if not self.node:
            self.status.text = "Reticulum not available"
            return
        self.status.text = f"Peers discovered: {len(self.node.get_discovered_peers())}"


class SettingsScreen(Box):
    def __init__(self, node):
        super().__init__()
        self.style.direction = COLUMN
        self.style.margin = 10
        self.node = node
        self.add(make_label("Settings", size=20, margin_b=10))

        h = self.node.get_identity_hash() if self.node else ""
        self.add(make_label(f"Hash:\n{h}" if h else "Hash:\nRNS not available", size=11, margin_b=12))

        announce_btn = Button("Announce Myself", on_press=self.announce)
        self.add(announce_btn)
        self.announce_label = Label("")
        self.add(self.announce_label)

        self.add(make_label("Interfaces", size=16, margin_b=6))
        self.add(Label("AutoInterface: Enabled"))
        self.add(make_label("Reticulum Mesh v0.2.0", size=10, margin_b=8))

    def announce(self, widget):
        if self.node:
            self.announce_label.text = "Announced!" if self.node.announce_myself() else "Failed"


class ReticulumMeshApp(App):
    def startup(self):
        self.main_window = MainWindow(title="Reticulum Mesh")
        self.node = MobileReticulumNode()

        self.content_box = Box()
        self.content_box.style.direction = COLUMN
        self.content_box.style.flex = 1

        self.screen_container = Box()
        self.screen_container.style.direction = COLUMN
        self.screen_container.style.flex = 1

        nav_bar = Box()
        nav_bar.style.direction = ROW
        nav_bar.style.margin = 4

        for name, key in [("Chat", "chat"), ("Contacts", "contacts"), ("Network", "network"), ("Settings", "settings")]:
            btn = Button(name, on_press=lambda w, k=key: self.show_screen(k))
            btn.style.flex = 1
            nav_bar.add(btn)

        self.content_box.add(self.screen_container)
        self.content_box.add(nav_bar)
        self.main_window.content = self.content_box
        self.main_window.show()

        self.show_screen("chat")

    def show_screen(self, screen_name):
        self.screen_container.clear()
        if screen_name == "chat":
            screen = MessagesScreen(self.node)
        elif screen_name == "contacts":
            screen = ContactsScreen(self.node)
        elif screen_name == "network":
            screen = NetworkScreen(self.node)
        elif screen_name == "settings":
            screen = SettingsScreen(self.node)
        else:
            screen = MessagesScreen(self.node)
        self.screen_container.add(screen)


def main():
    return ReticulumMeshApp()
